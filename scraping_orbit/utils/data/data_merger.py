import os
import traceback
import pandas as pd
from scraping_orbit.utils.data.dataframe_functions import concat_dataframes_v2


def merge_data_files(file_list: list,
                     file_extension: str,
                     drop_duplicates: bool = False,
                     drop_duplicates_column: str = '',
                     keep_duplicates: str = 'first',
                     delimiter=',',
                     encoding='utf8',
                     delete_local_files=False,
                     read_specific_columns=False,
                     column_list=None):
    """
    Merges data from multiple files into a single DataFrame.

    Args:
        file_list (list): List of file paths to merge.
        file_extension (str): Extension of files to merge ('csv', 'parquet', 'json').
        drop_duplicates (bool): Whether to drop duplicates from the merged DataFrame.
        drop_duplicates_column (str): Column name(s) to check for duplicates.
        keep_duplicates (str): Which duplicates to keep ('first', 'last').
        delimiter (str): Delimiter for CSV files.
        encoding (str): Encoding for CSV files.
        delete_local_files (bool): Whether to delete local files after merging.
        read_specific_columns (bool): Whether to read only specific columns.
        column_list (list): List of columns to read if read_specific_columns is True.

    Returns:
        pd.DataFrame: Merged DataFrame.
    """
    if column_list is None:
        column_list = ['']

    merged_df = None

    if not delimiter:
        delimiter = ','
    if not encoding:
        encoding = 'utf-8'
    if not keep_duplicates:
        keep_duplicates = 'last'

    if not file_list:
        return merged_df

    problematic_dfs = []
    dataframe_list = []

    for file in file_list:
        try:
            if 'parquet' in file_extension:
                df = pd.read_parquet(file, columns=column_list if read_specific_columns else None, engine='pyarrow')
                dataframe_list.append(df)
            elif 'csv' in file_extension:
                df = pd.read_csv(file, delimiter=delimiter, encoding=encoding, on_bad_lines='warn')
                dataframe_list.append(df)
            elif 'json' in file_extension:
                df = pd.read_json(file)
                dataframe_list.append(df)
        except Exception as e:
            print(f"Error reading {file}: {e}")
            print(traceback.format_exc())

        if delete_local_files:
            try:
                os.remove(file)
            except Exception as e:
                print(f"Error deleting {file}: {e}")

    try:
        merged_df = concat_dataframes_v2(dfs=dataframe_list)
        if drop_duplicates:
            if not drop_duplicates_column:
                merged_df.drop_duplicates(inplace=True)
            else:
                columns = [col.strip() for col in drop_duplicates_column.split(',')]
                if not set(columns).issubset(merged_df.columns):
                    print(f"Some columns {columns} do not exist in the DataFrame. Performing default drop duplicates.")
                    merged_df.drop_duplicates(inplace=True)
                else:
                    merged_df.drop_duplicates(subset=columns, keep=keep_duplicates, inplace=True)
    except Exception as e:
        print(f"Error merging dataframes: {e}")
        print(traceback.format_exc())

    return merged_df
