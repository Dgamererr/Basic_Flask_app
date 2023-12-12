import pandas as pd
import numpy as np

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

def apply_buckets(df, buckets, 
                  p1_to_adjust, initial_p1, p2_to_adjust, initial_p2,
                  AP_Index):

    df.sort_values(by='PRICE_INDEX_NUM', inplace=True)
    df = df.reset_index(drop=True)
    adjusted = False

    print('AP index in function ', AP_Index)    

    for colb, I_Start in zip(buckets, AP_Index):
        last_adjusted_index = None
        cumulative_sum = 0
        for index_price_num, row in df.iterrows():
            print('function istart : ', I_Start)
            if index_price_num < I_Start:
                df.at[index_price_num, colb] = np.nan
            else:
                if row[colb] < 0:
                    df.at[index_price_num, colb] = 0
                    adjusted = True
                cumulative_sum += row[colb]
                if cumulative_sum > 100:#Fill remainder into rest of cells
                    excess = cumulative_sum - 100
                    df.at[index_price_num, colb] -= excess
                    cumulative_sum = 100  # Reset cumulative sum to 100 after adjustment
                    last_adjusted_index = index_price_num
                    adjusted = True
                elif not adjusted:
                    last_adjusted_index = index_price_num  # Update last index before adjustment

            # Step 1: Identify rows with zero values
        zero_value_indices = df.index[df[colb] == 0].tolist()


        # Calculate the remaining value
        remaining_value = 100 - cumulative_sum

        if remaining_value > 0:
            # Check for zero-value rows
            zero_value_indices = df.index[df[colb] == 0].tolist()
            adjusted = True
            if zero_value_indices:
                # If there are zero-value rows, distribute among them
                distribute_indices = zero_value_indices
            else:
                # Otherwise, distribute among all rows
                distribute_indices = df.index.tolist()

            # Distribute the remaining value equally
            equal_distribution = remaining_value // len(distribute_indices)
            remainder = remainder = int(remaining_value % len(distribute_indices))


            # Sort indices by value in the column for distributing the remainder
            sorted_indices_by_value = df[colb].sort_values().index

            # Update the DataFrame
            for index in distribute_indices:
                df.at[index, colb] += equal_distribution
                # Distribute the remainder, starting with the lowest value
                if index in sorted_indices_by_value[:remainder]:
                    df.at[index, colb] += 1
    
    def adjust_params(df, buckets, p_to_adjust, initial_p, AP_Index):
        df.fillna(0, inplace=True)
        for (colb,colp, IStart) in zip(buckets, p_to_adjust, AP_Index):
            started = False  # Flag to indicate if the process has started
            for i in range(len(df)):
                if i < IStart:
                    df.at[df.index[i], colp] = 9
                if not started and i >= IStart:
                    # Start the process here
                    new_value = initial_p- (initial_p * (df.at[df.index[i], colb] / 100)).round(2)
                    df.at[df.index[i], colp] = round(max(new_value, 0), 2)
                    started = True
                elif started:
                    # Continue the process as before
                    new_value = df.at[df.index[i - 1], colp] - (initial_p * (df.at[df.index[i], colb] / 100)).round(2)
                    df.at[df.index[i], colp] = round(max(new_value, 0), 2)
                
            if started:
                # Set the last 'P1' value to 0
                df.at[df.index[-1], colp] = 0

        return df

    df = adjust_params(df, buckets, p1_to_adjust, initial_p1, AP_Index)
    df = adjust_params(df, buckets, p2_to_adjust, initial_p2, AP_Index)

    return df, adjusted



def get_param_data():
    df_raw = pd.read_csv(rf'/Users/danielchung/Downloads/TIP PARAM - Sheet1.csv')

    return df_raw

def format_data(df):
    # Convert the 'your_column' from float to int
    df.dropna(inplace=True)
    df['AP_INV'] = df['AP_INV'].astype(int)
    df['PRICE_INDEX_NUM'] = df['PRICE_INDEX_NUM'].astype(int)

    pivot_df = df.pivot_table(
        index=["PRICE_INDEX", "PRICE_INDEX_NUM", "ROUTE", "INVENTORY_CARRIER_CD"],
        columns=["AP_INV", "P_OPTION"],
        values=["P_PCT"],
        aggfunc='max'
    )

    pivot_df2 = df.pivot_table(
        index=["PRICE_INDEX", "PRICE_INDEX_NUM", "ROUTE", "INVENTORY_CARRIER_CD"],
        columns=["AP_INV"],
        values=["BUCKETS"],
        aggfunc='max'
    )

    # Flatten the multi-level column index by joining the levels with an underscore
    # This also trims any excess padding that might cause additional underscores
    pivot_df.columns = ['_'.join(str(level).strip() for level in col).rstrip('_') for col in pivot_df.columns.values]
    pivot_df2.columns = ['_'.join(str(level).strip() for level in col).rstrip('_') for col in pivot_df2.columns.values]

    merged_df = pd.merge(pivot_df, pivot_df2, on=["PRICE_INDEX", "PRICE_INDEX_NUM", "ROUTE", "INVENTORY_CARRIER_CD"], how="left")
    # Reset the index to make the DataFrame flat
    merged_df = merged_df.reset_index()

    # Flatten the multi-level column index by joining the levels with an underscore
    # This also trims any excess padding that might cause additional underscores
    pivot_df.columns = ['_'.join(str(level).strip() for level in col).rstrip('_') for col in pivot_df.columns.values]
    pivot_df2.columns = ['_'.join(str(level).strip() for level in col).rstrip('_') for col in pivot_df2.columns.values]

    df_param = merged_df[['PRICE_INDEX', 'PRICE_INDEX_NUM', 'ROUTE', 'INVENTORY_CARRIER_CD', 'P_PCT_180_P1', 'P_PCT_180_P2', 'BUCKETS_180', 'P_PCT_120_P1', 'P_PCT_120_P2', 'BUCKETS_120' ,'P_PCT_100_P1', 'P_PCT_100_P2', 'BUCKETS_100']]

    df_param.loc[df_param['P_PCT_180_P1'] == 9, 'BUCKETS_180'] = 0
    df_param.loc[df_param['P_PCT_120_P1'] == 9, 'BUCKETS_120'] = 0
    df_param.loc[df_param['P_PCT_100_P1'] == 9, 'BUCKETS_100'] = 0

    df_param.sort_values(by = 'PRICE_INDEX_NUM', inplace=True)
    return df_param

def filter_data(data_list, filter_dict):
    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)

    # Apply filtering
    for column, value in filter_dict.items():
        if column in df.columns:
            df = df[df[column] == value]

    # Convert the filtered DataFrame back to a list of dictionaries
    filtered_data_list = df.to_dict(orient='records')

    return filtered_data_list


def update_base_data(base, user):
    df = pd.DataFrame(base)
    df2 = pd.DataFrame(user)

    df2.fillna(-91, inplace=True)

    print(df.head(16))
    print(df2.head(16))

    # Set the specified columns as index
    index_columns = ['PRICE_INDEX', 'PRICE_INDEX_NUM', 'ROUTE', 'INVENTORY_CARRIER_CD']
    df.set_index(index_columns, inplace=True)
    df2.set_index(index_columns, inplace=True)

    # Update df with the values from df2
    df.update(df2, overwrite=True)

    df.replace(-91, 0, inplace=True)

    # Reset the index if necessary
    df.reset_index(inplace=True)

    return df

def update_base_metadata(base, user):
    df = pd.DataFrame(base)
    df2 = pd.DataFrame(user)

    print('base ', df)
    print('user ', df2)

    # Set the specified columns as index
    index_columns = ['ROUTE', 'INVENTORY_CARRIER_CD', 'AP', 'PARAMETER_NO']
    df.set_index(index_columns, inplace=True)
    df2.set_index(index_columns, inplace=True)
    # Update df with the values from df2
    df.update(df2)

    # Reset the index if necessary
    df.reset_index(inplace=True)

    return df

