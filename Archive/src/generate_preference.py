"""
This is the second script in a series of 3. This script takes a parking demand
generator shapefile and a parking supply shapefile as input. The files are projected
into GCS WGS 1984 then the parking supply shapefile is spatial joined with the demand
generators.

All of the parking locations within the specified distance threshold are joined to each
generator. The distance between generator and each lot is calculated then ranked in
order from closest lot to furthest lot. Finally a lot preference csv is exported.

"""

import logging

import pandas as pd
import geopandas as gpd

LOT_DIST_COL = "lot_distance"
PRIVATE_LOT_COL = "private_lot"
COST_COL = "cost"

LOGGER = logging.getLogger("Generate Preference")


def join_generators_to_lots(
    demand_gdf, supply_gdf, projected_crs, buffer_dist, lot_capacity_col, gen_size_col
):
    """One-to-many spatial join of generators to lots"""

    supply_len = len(supply_gdf)
    supply_gdf = supply_gdf[supply_gdf[lot_capacity_col] > 0]
    LOGGER.info(f"removed {supply_len - len(supply_gdf)} lots with zero capacity")

    demand_len = len(demand_gdf)
    demand_gdf = demand_gdf[demand_gdf[gen_size_col] > 0]
    LOGGER.info(f"removed {demand_len - len(demand_gdf)} generators with zero demand")

    demand_gdf = demand_gdf.to_crs(projected_crs)
    supply_gdf = supply_gdf.to_crs(projected_crs)

    supply_gdf["lot_geometry"] = supply_gdf["geometry"]
    supply_gdf["geometry"] = supply_gdf.buffer(buffer_dist)

    joined_gdf = gpd.sjoin(demand_gdf, supply_gdf)

    # include distance to closest lots
    joined_gdf[LOT_DIST_COL] = joined_gdf["geometry"].distance(
        joined_gdf["lot_geometry"]
    )

    joined_gdf.drop(["geometry", "lot_geometry"], axis=1, inplace=True)

    return joined_gdf


def generate_preference(
    gen_lot_df,
    factors_df,
    lot_res_codes,
    restrict_col,
    gen_id_col,
    lot_id_col,
    lot_gen_id_col,
    lot_luc_col,
    day_col,
    month_col,
    hour_col,
    restrict_df=None,
):
    """
    Filter lot availability according to restriction codes.

    --------------
    Restrict Codes
    --------------

    0: No restrictions
    1: Restricted to single generator ID
    2: Commercial only
    3: Restricted to generators in lookup table
    4: Same as code 3 but only available between 9am and 6pm weekdays
    5: Metered parking. Adds cost to lot.
    6: Same as 5 but only available between 9am and 6pm weekdays

    Parameters
    ----------

    gen_lot_df: combined generator/lot df from join_generators_to_lots
    lot_res_codes: list of landuse codes designating residential zones
    restrict_col: column name of restricted lot codes (0: open, 1: residential, 2: business)
    gen_id_col: column name of generator ID
    lot_id_col: column name of lot ID
    lot_gen_id: column name of lot's generator ID
    lot_luc_col: column name of lot's landuse code
    """

    for col in [
        restrict_col,
        gen_id_col,
        lot_id_col,
        lot_gen_id_col,
        lot_luc_col,
        LOT_DIST_COL,
    ]:

        assert col in gen_lot_df, f"{col} not in gen_lot_df"

    gen_dist_df = gen_lot_df.sort_values([gen_id_col, LOT_DIST_COL], ascending=True)

    original_length = len(gen_dist_df)
    LOGGER.debug(f"total generator/lot pairs: {original_length}")

    ### Time-independent restrictions ###

    # Restrict Code 1: Remove residental-only lots for non-residents
    gen_dist_df = gen_dist_df[
        ~(
            (gen_dist_df[restrict_col] == 1)
            & (gen_dist_df[gen_id_col] != gen_dist_df[lot_gen_id_col])
        )
    ]

    updated_length = len(gen_dist_df) - original_length
    LOGGER.debug(f"removed {updated_length} invalid residential pairs")

    # Restrict Code 1: Prioritize private lots for residents
    gen_dist_df[PRIVATE_LOT_COL] = 0.0
    gen_dist_df.loc[
        (gen_dist_df[restrict_col] == 1)
        & (gen_dist_df[gen_id_col] == gen_dist_df[lot_gen_id_col])
        & (gen_dist_df[lot_luc_col].isin(lot_res_codes)),
        PRIVATE_LOT_COL,
    ] = 1.0

    # Restrict Code 2: Remove business lots in residential zones
    gen_dist_df = gen_dist_df[
        ~(
            (gen_dist_df[restrict_col] == 2)
            & (gen_dist_df[lot_luc_col].isin(lot_res_codes))
        )
    ]

    updated_length = len(gen_dist_df) - updated_length
    LOGGER.debug(f"removed {updated_length} invalid zone combinations")

    if restrict_df is not None:

        # Restrict Code 3: Filter gen-lot combos in lookup table
        assert lot_id_col in restrict_df
        assert gen_id_col in restrict_df

        restrict_3 = gen_dist_df[restrict_col] == 3
        restrict_3_df = gen_dist_df[restrict_3].copy()

        gen_dist_df = gen_dist_df[~restrict_3]
        restrict_3_df = restrict_3_df.merge(
            restrict_df[[lot_id_col, gen_id_col]],
            on=[lot_id_col, gen_id_col],
            how="inner",
        )

        gen_dist_df = pd.concat([gen_dist_df, restrict_3_df])

        updated_length = len(gen_dist_df) - updated_length
        LOGGER.debug(f"Restrict code 3 table: removed {updated_length} lot/gen pairs")

    # Restrict Code 5: All day metered parking
    if COST_COL not in gen_dist_df:
        gen_dist_df[COST_COL] = 0.0

    gen_dist_df.loc[gen_dist_df[restrict_col] == 5, COST_COL] = 1.0

    # expand to timeseries for following restrict codes
    lot_pref_df = factors_df.merge(gen_dist_df, on=lot_luc_col, how="outer").dropna()

    if restrict_df is not None:

        orig_length = len(lot_pref_df)

        restrict_4 = (
            (lot_pref_df[restrict_col] == 4)
            & (lot_pref_df[day_col] == "Weekday")
            & (lot_pref_df[hour_col] >= 9)
            & (lot_pref_df[hour_col] < 18)
        )

        restrict_4_df = lot_pref_df[restrict_4].copy()

        lot_pref_df = lot_pref_df[~restrict_4]
        restrict_4_df = restrict_4_df.merge(
            restrict_df[[lot_id_col, gen_id_col]],
            on=[lot_id_col, gen_id_col],
            how="inner",
        )

        lot_pref_df = pd.concat([lot_pref_df, restrict_4_df])

        updated_length = len(lot_pref_df) - orig_length
        LOGGER.debug(f"Restrict code 4 table: removed {updated_length} lot/gen pairs")

    # Restrict Code 6: 9 to 6 metered parking
    lot_pref_df.loc[
        (lot_pref_df[restrict_col] == 6)
        & (lot_pref_df[day_col] == "Weekday")
        & (lot_pref_df[hour_col] >= 9)
        & (lot_pref_df[hour_col] < 18),
        COST_COL,
    ] = 1.0

    return lot_pref_df


def run(configs, factors_df=None):

    demand_filename = configs.get("demand_shapefile")
    supply_filename = configs.get("supply_shapefile")

    demand_gdf = configs.read_shapefile(demand_filename)
    supply_gdf = configs.read_shapefile(supply_filename)

    max_dist = configs.get("max_walk_dist")
    capacity_col = configs.get("lot_capacity_col")
    gen_size_col = configs.get("gen_size_col")

    gen_lot_df = join_generators_to_lots(
        demand_gdf,
        supply_gdf,
        configs.get("projected_crs"),
        max_dist,
        capacity_col,
        gen_size_col,
    )

    lot_luc_col = configs.get("lot_luc_col")
    lot_id_col = configs.get("lot_id_col")
    gen_id_col = configs.get("gen_id_col")
    lot_gen_id_col = configs.get("lot_gen_id_col")
    restrict_col = configs.get("restrict_col")

    gen_lot_df = gen_lot_df[
        [
            lot_luc_col,
            lot_id_col,
            gen_id_col,
            lot_gen_id_col,
            gen_size_col,
            capacity_col,
            restrict_col,
            LOT_DIST_COL,
        ]
    ]

    gen_lot_file = configs.get("gen_lot_filename")
    configs.write_dataframe(gen_lot_df, gen_lot_file)

    lot_res_codes = configs.get("restricted_lot_landuse_codes")
    lot_restrict_file = configs.get("lot_restrict_file")

    if lot_restrict_file is not None:
        restrict_df = configs.read_input_dataframe(lot_restrict_file)
    else:
        restrict_df = None

    if factors_df is None:
        factors_file = configs.get("factors_filename")
        factors_df = configs.read_output_dataframe(factors_file)

    month_col = configs.get("month_col")
    day_col = configs.get("day_col")
    hour_col = configs.get("hour_col")

    lot_pref_df = generate_preference(
        gen_lot_df,
        factors_df,
        lot_res_codes=lot_res_codes,
        restrict_col=restrict_col,
        gen_id_col=gen_id_col,
        lot_id_col=lot_id_col,
        lot_gen_id_col=lot_gen_id_col,
        lot_luc_col=lot_luc_col,
        month_col=month_col,
        day_col=day_col,
        hour_col=hour_col,
        restrict_df=restrict_df,
    )

    lot_pref_file = configs.get("preference_filename")
    configs.write_dataframe(lot_pref_df, lot_pref_file)
