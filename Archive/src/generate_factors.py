"""
Creates pandas DataFrame of factors.

Contains every combination of factors related to shared parking, indexed by zone
index and timestamp
"""

import pandas as pd


def expand_typicals(df, target_col, typical_str, labels=None, index_cols=None):
    """If a DataFrame column contains a 'Typical' entry, duplicate the row for every
    category in `labels`
    """

    if not labels:
        labels = list(df[target_col].unique())
        labels.remove(typical_str)

    not_typical = df[df[target_col] != typical_str]
    typical = df[df[target_col] == typical_str]

    df_parts = []
    df_parts.append(not_typical)

    for label in labels:

        df_part = typical.copy()
        df_part[target_col] = label

        df_parts.append(df_part)

    expanded_df = pd.concat(df_parts)

    if index_cols:

        expanded_df = expanded_df.drop_duplicates(subset=index_cols)

    else:

        expanded_df = expanded_df.drop_duplicates()

    return expanded_df


def generate_factors(
    monthly_df,
    daily_df,
    hourly_df,
    months,
    days,
    hours,
    luc_col="LUC",
    user_col="User",
    month_col="Month",
    day_col="Day",
    hour_col="Hour",
    typical_str="Typical",
    fill_missing=1.0,
):

    monthly_melt = monthly_df.melt(
        id_vars=[luc_col, user_col, day_col],
        value_vars=months,
        var_name=month_col,
        value_name=f"{month_col}_factor",
    )

    daily_melt = daily_df.melt(
        id_vars=[luc_col, user_col],
        value_vars=days,
        var_name=day_col,
        value_name=f"{day_col}_factor",
    )

    hourly_melt = hourly_df.melt(
        id_vars=[luc_col, user_col, month_col, day_col],
        value_vars=hours,
        var_name=hour_col,
        value_name=f"{hour_col}_factor",
    )

    monthly_expanded = expand_typicals(
        df=monthly_melt,
        target_col=day_col,
        typical_str=typical_str,
        index_cols=[luc_col, user_col, month_col, day_col],
    )

    hourly_expanded = expand_typicals(
        df=hourly_melt,
        target_col=month_col,
        typical_str=typical_str,
        labels=months,
        index_cols=[luc_col, user_col, month_col, day_col, hour_col],
    )

    # No need to expand daily typicals for now
    factors_df = hourly_expanded.merge(
        daily_melt, how="outer", on=[luc_col, user_col, day_col]
    )

    factors_df = factors_df.merge(
        monthly_expanded, how="outer", on=[luc_col, user_col, month_col, day_col]
    )

    if fill_missing:

        factors_df = factors_df.fillna(fill_missing)

    else:

        factors_df = factors_df.dropna()

    factors_df["factor"] = factors_df[
        [f"{month_col}_factor", f"{day_col}_factor", f"{hour_col}_factor"]
    ].prod(axis=1)

    factors_df = factors_df.groupby(
        [luc_col, month_col, day_col, hour_col], as_index=False
    )["factor"].sum()

    return factors_df


def run(configs):

    input_xlsx = configs.get("factors_file")
    monthly_df = configs.read_excel_sheet(input_xlsx, configs.get("monthly_sheetname"))
    daily_df = configs.read_excel_sheet(input_xlsx, configs.get("daily_sheetname"))
    hourly_df = configs.read_excel_sheet(input_xlsx, configs.get("hourly_sheetname"))

    factors_df = generate_factors(
        monthly_df,
        daily_df,
        hourly_df,
        months=configs.get("months"),
        days=configs.get("days"),
        hours=configs.get("hours"),
        luc_col=configs.get("landuse_code_col"),
        user_col=configs.get("user_col"),
        month_col=configs.get("month_col"),
        day_col=configs.get("day_col"),
        hour_col=configs.get("hour_col"),
        typical_str=configs.get("typical_str"),
        fill_missing=configs.get("fill_missing_factors"),
    )

    factors_filename = configs.get("factors_filename")
    configs.write_dataframe(factors_df, factors_filename)
