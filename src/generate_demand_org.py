import logging

import numpy as np

from .generate_preference import (
    LOT_DIST_COL,
    PRIVATE_LOT_COL,
    COST_COL
)

LOT_DEMAND_COL = "lot_demand"
GEN_LOT_DEMAND_COL = "demand"
UTILITY_COL = "utility"
WEIGHT_COL = "weight"
LEFTOVER_SPACE_COL = "free_space"
OVERFLOW_COL = "overflow"

LOGGER = logging.getLogger("Generate Demand")


def calculate_utility(
    pref_df,
    lot_capacity_col,
    gen_size_col,
    lot_agg_cols,
    gen_agg_cols,
    max_dist,
    distance_factor=1.0,
    capacity_factor=1.0,
    scarcity_factor=1.0,
    private_lot_factor=0.0,
    cost_factor=1.0
):
    """Add lot-choice fraction to generators using utility choice model"""

    # Determine total demand near a particular lot
    demand_df = pref_df.join(
        pref_df.groupby(lot_agg_cols)[gen_size_col].sum().rename(LOT_DEMAND_COL),
        on=lot_agg_cols,
    )

    demand_df["demand_ratio"] = demand_df[LOT_DEMAND_COL]/demand_df[lot_capacity_col]

    # Add chooser columns summed over generator IDs
    demand_df = demand_df.join(
        demand_df.groupby(gen_agg_cols)[
            [LOT_DIST_COL]
        ].sum(),
        on=gen_agg_cols,
        rsuffix="_sum",
    )

    demand_df = demand_df.join(
        demand_df.groupby(gen_agg_cols)[
            [lot_capacity_col,f"demand_ratio"]
            ].max(),
        on=gen_agg_cols,
        rsuffix="_max",
    )


    

    # Define distance score as inverse of gen-to-lot distance relative to all lots
    demand_df["distance_score"] = (
        (-1)/(1+np.exp(((max_dist/2)-demand_df[LOT_DIST_COL])/(max_dist/6)))) * distance_factor



    # Weight lots by relative size
    demand_df["capacity_score"] = (
        demand_df[lot_capacity_col] / demand_df[f"{lot_capacity_col}_max"] - 1
    ) * capacity_factor

    # Weight lots by inverse of popularity
    demand_df["lot_demand_score"] = 0 - (
        (demand_df[f"demand_ratio"] / demand_df[f"demand_ratio_max"])
        * scarcity_factor
    )

    # Weight lots by private access
    demand_df["private_lot_score"] = demand_df[PRIVATE_LOT_COL] * private_lot_factor

    demand_df["cost_score"] = (
        demand_df[COST_COL] * cost_factor * (-1)
    )

    demand_df.fillna({"cost_score": 0}, inplace=True)

    demand_df[UTILITY_COL] = np.exp(
        demand_df[
            [
                "distance_score",
                "capacity_score",
                "lot_demand_score",
                "private_lot_score",
                "cost_score",
            ]
        ].sum(axis=1)
    )

    demand_df = demand_df.join(
        demand_df.groupby(gen_agg_cols)[UTILITY_COL].sum(),
        on=gen_agg_cols,
        rsuffix="_sum",
    )

    # Lot choice is weighted by sum of utility for all lots
    demand_df[WEIGHT_COL] = demand_df[UTILITY_COL] / demand_df["utility_sum"]

    return demand_df


def create_lot_timeseries(
    demand_df,
    lot_capacity_col,
    lot_agg_cols,
):

    # Sum demand (cars in lot) over all lots
    ts_df = demand_df.groupby(
        lot_agg_cols,
        as_index=False,
    ).agg({lot_capacity_col: "first", GEN_LOT_DEMAND_COL: "sum"})

    return ts_df


def add_overflow_cols(ts_df, capacity_col):

    ts_df[OVERFLOW_COL] = ts_df[GEN_LOT_DEMAND_COL] - ts_df[capacity_col]
    ts_df.loc[ts_df[OVERFLOW_COL] < 0, OVERFLOW_COL] = 0
    ts_df[LEFTOVER_SPACE_COL] = ts_df[capacity_col] - ts_df[GEN_LOT_DEMAND_COL]
    ts_df.loc[ts_df[LEFTOVER_SPACE_COL] < 0, LEFTOVER_SPACE_COL] = 0
    ts_df[GEN_LOT_DEMAND_COL] = ts_df[[GEN_LOT_DEMAND_COL, capacity_col]].min(axis=1)


def redistribute_overflow(
    orig_ts_df,
    pref_df,
    lot_id_col,
    gen_id_col,
    lot_gen_id_col,
    capacity_col,
    gen_size_col,
    datetime_cols,
    distance_factor,
    capacity_factor,
    scarcity_factor,
    private_lot_factor,
    cost_factor,
):

    orig_ts_df = orig_ts_df[
        [
            lot_id_col,
            capacity_col,
            GEN_LOT_DEMAND_COL,
        ]
        + datetime_cols
    ]
    pref_df = pref_df[
        [gen_id_col, lot_id_col, lot_gen_id_col, LOT_DIST_COL, PRIVATE_LOT_COL]
    ]

    # determine overflow
    new_ts_df = orig_ts_df.copy()
    add_overflow_cols(new_ts_df, capacity_col)

    lot_gen_agg_cols = datetime_cols + [lot_gen_id_col]
    lot_agg_cols = datetime_cols + [lot_id_col]
    gen_agg_cols = datetime_cols + [gen_id_col]

    # repurpose overflow as generator size for new iteration
    demand_df = new_ts_df.merge(pref_df, on=lot_id_col, how="inner")
    demand_df = demand_df[demand_df[lot_gen_id_col] > 0]

    demand_df = demand_df.join(
        demand_df.groupby(lot_gen_agg_cols)[OVERFLOW_COL].sum().rename(gen_size_col),
        on=gen_agg_cols,
    )

    total_pairs = len(demand_df)

    # keep generators with overflow and lots with space leftover
    demand_df = demand_df[
        (demand_df[gen_size_col] > 0) & (demand_df[LEFTOVER_SPACE_COL] > 0)
    ]

    overflow_pairs = len(demand_df)
    overflow_pct = (overflow_pairs * 100) / total_pairs
    LOGGER.info(
        f"redistributing overflow for {overflow_pairs} "
        f"({overflow_pct:.2f}%) generator/lot pairs"
    )

    demand_df = calculate_utility(
        demand_df,
        lot_capacity_col=LEFTOVER_SPACE_COL,
        gen_size_col=gen_size_col,
        lot_agg_cols=lot_agg_cols,
        gen_agg_cols=gen_agg_cols,
        max_dist=max_dist,
        distance_factor=distance_factor,
        capacity_factor=capacity_factor,
        scarcity_factor=scarcity_factor,
        private_lot_factor=private_lot_factor,
        cost_factor=cost_factor,
    )

    demand_df[GEN_LOT_DEMAND_COL] = demand_df[[gen_size_col, WEIGHT_COL]].prod(axis=1)

    orig_ts_df[GEN_LOT_DEMAND_COL] = orig_ts_df[[capacity_col, GEN_LOT_DEMAND_COL]].min(
        axis=1
    )

    new_ts_df = create_lot_timeseries(
        demand_df,
        lot_capacity_col=LEFTOVER_SPACE_COL,
        lot_agg_cols=lot_agg_cols,
    )

    final_ts_df = orig_ts_df.merge(
        new_ts_df, how="left", on=lot_agg_cols, suffixes=["_orig", "_new"]
    ).fillna(0)

    final_ts_df[GEN_LOT_DEMAND_COL] = final_ts_df[
        [f"{GEN_LOT_DEMAND_COL}_orig", f"{GEN_LOT_DEMAND_COL}_new"]
    ].sum(axis=1)

    return final_ts_df


def run(configs, pref_df=None):

    if pref_df is None:
        preference_file = configs.get("preference_filename")
        pref_df = configs.read_output_dataframe(preference_file)

    lot_id_col = configs.get("lot_id_col")
    gen_id_col = configs.get("gen_id_col")
    lot_gen_id_col = configs.get("lot_gen_id_col")
    capacity_col = configs.get("lot_capacity_col")
    gen_size_col = configs.get("gen_size_col")
    month_col = configs.get("month_col")
    day_col = configs.get("day_col")
    hour_col = configs.get("hour_col")
    distance_factor = configs.get("distance_factor")
    capacity_factor = configs.get("capacity_factor")
    scarcity_factor = configs.get("scarcity_factor")
    private_lot_factor = configs.get("private_lot_factor")
    cost_factor = configs.get("cost_factor")
    max_dist = configs.get("max_walk_dist")

    lot_agg_cols = [lot_id_col, month_col, day_col, hour_col]
    gen_agg_cols = [gen_id_col, month_col, day_col, hour_col]

    LOGGER.info("calculating utility...")
    demand_df = calculate_utility(
        pref_df,
        lot_capacity_col=capacity_col,
        gen_size_col=gen_size_col,
        lot_agg_cols=lot_agg_cols,
        gen_agg_cols=gen_agg_cols,
        max_dist=max_dist,
        distance_factor=distance_factor,
        capacity_factor=capacity_factor,
        scarcity_factor=scarcity_factor,
        private_lot_factor=private_lot_factor,
        cost_factor=cost_factor,
    )

    demand_df[GEN_LOT_DEMAND_COL] = demand_df[
        [gen_size_col, WEIGHT_COL, "factor"]
    ].prod(axis=1)

    demand_file = configs.get("demand_filename")
    configs.write_dataframe(demand_df, demand_file)

    LOGGER.info("creating lot timeseries...")
    ts_df = create_lot_timeseries(
        demand_df,
        lot_capacity_col=capacity_col,
        lot_agg_cols=lot_agg_cols,
    )

    if configs.get("redistribute_overflow"):

        ts_df = redistribute_overflow(
            ts_df,
            pref_df,
            lot_id_col=lot_id_col,
            gen_id_col=gen_id_col,
            lot_gen_id_col=lot_gen_id_col,
            capacity_col=capacity_col,
            gen_size_col=gen_size_col,
            datetime_cols=[month_col, day_col, hour_col],
            distance_factor=distance_factor,
            capacity_factor=distance_factor,
            scarcity_factor=scarcity_factor,
            private_lot_factor=private_lot_factor,
            cost_factor=cost_factor,
        )

    add_overflow_cols(ts_df, capacity_col)

    ts_df = ts_df[
        [lot_id_col, month_col, day_col, hour_col, capacity_col, GEN_LOT_DEMAND_COL]
    ]

    ts_df["frac_full"] = ts_df[GEN_LOT_DEMAND_COL] / ts_df[capacity_col]

    timeseries_file = configs.get("timeseries_filename")
    configs.write_dataframe(ts_df, timeseries_file)
