import pandas as pd

# Sort the 'AP_INV' level of the columns in descending order while keeping 'P_OPTION' in ascending order
# Create a custom sort function for this
def custom_sort(df, level_1_desc, level_2_asc):
    # Get the MultiIndex levels
    level_1, level_2 = df.columns.levels
    # Sort the first level in descending order
    level_1_sorted = sorted(level_1, reverse=True)
    # Sort the second level in ascending order
    level_2_sorted = sorted(level_2)
    # Create a new MultiIndex with the product of the sorted levels
    new_index = pd.MultiIndex.from_product([level_1_sorted, level_2_sorted], names=df.columns.names)
    # Reindex the DataFrame with the new MultiIndex
    df = df.reindex(columns=new_index)
    return df

def adjust_decreasing_values(df, columns):
    # Sort DataFrame by PRICE_INDEX_NUM
    df = df.sort_values(by='PRICE_INDEX_NUM')
    changes_made = False  # Flag to track changes

    for i in range(1, len(df)):
        for col in columns:
            if df.at[i, col] > df.at[i - 1, col]:
                df.at[i, col] = df.at[i - 1, col]
                changes_made = True  # Set flag if a change is made

    return df, changes_made

def get_data():
    df_raw=pd.read_csv(rf'/Users/danielchung/Downloads/TIP PARAM - Sheet1.csv')

    return df_raw

def format_data(df):
    df_raw = df[df['INVENTORY_CARRIER_CD']=="BA"]

    df_param = df_raw.pivot_table(
        index=["PRICE_INDEX", "PRICE_INDEX_NUM", "ROUTE", "INVENTORY_CARRIER_CD"],
        columns=["AP_INV", "P_OPTION"],
        values="P_PCT",
        aggfunc='max'
    )


    # Apply the custom sorting function
    df_param= custom_sort(df_param, 'AP_INV', 'P_OPTION')

    # Flatten the multi-level column index by joining the levels with an underscore
    # This also trims any excess padding that might cause additional underscores
    df_param.columns = ['_'.join(str(level).strip() for level in col).rstrip('_') for col in df_param.columns.values]

    df_param.sort_values(by = "PRICE_INDEX_NUM", inplace=True)

    df_test = df_param.copy()
    print(df_param)

    # Reset the index to make the DataFrame flat
    df_param = df_param.reset_index()

    return df_param


