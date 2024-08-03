import logging
import pandas as pd
import pyarrow as pa
from pyarrow import parquet as pyaparquet, csv as pyacsv

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)


def concat_dataframes(df_list):
    """
    Concatenate a list of dataframes using a common schema.

    Args:
        df_list (list): List of dataframes.

    Returns:
        pd.DataFrame: Concatenated dataframe.
    """
    common_schema = identify_common_schema(df_list)
    concatenated_dfs = []

    for df in df_list:
        try:
            dtype_mapping = {col: common_schema[col] for col in common_schema.index}
            df = df.astype(dtype_mapping)
            concatenated_dfs.append(df)
        except ValueError:
            logging.warning(
                f"Failed to convert dataframe with schema {df.dtypes} to common schema {common_schema}. "
                f"This dataframe will be skipped."
            )
            extra_columns = list(set(df.columns) - set(common_schema.index))
            if extra_columns:
                logging.warning(f"Extra columns {extra_columns} in dataframe will be added as object dtype.")
                df = df.astype({col: object for col in extra_columns})
            concatenated_dfs.append(df)

    if not concatenated_dfs:
        logging.error("All dataframes failed to convert to a common schema.")
        return None

    result = pd.concat(concatenated_dfs, ignore_index=True)
    return result


def concat_dataframes_v2(df_list):
    """
    Concatenate a list of dataframes using a common schema and add extra columns.

    Args:
        df_list (list): List of dataframes.

    Returns:
        pd.DataFrame: Concatenated dataframe.
    """
    schemas = [df.dtypes for df in df_list]
    common_schema = pd.concat(schemas, axis=1).mode(axis=1)[0]

    adjusted_dfs = []
    for df in df_list:
        extra_columns = pd.DataFrame(columns=list(set(common_schema.index) - set(df.columns)))
        adjusted_df = pd.concat([df, extra_columns], axis=1)
        adjusted_df = adjusted_df.astype(common_schema)
        adjusted_dfs.append(adjusted_df)

    concatenated_df = pd.concat(adjusted_dfs, ignore_index=True)
    return concatenated_df


def identify_common_schema(df_list):
    """
    Identify a common schema from a list of dataframes.

    Args:
        df_list (list): List of dataframes.

    Returns:
        pd.Series: Common schema.
    """
    schemas = [df.dtypes for df in df_list]
    common_schema = schemas[0]

    for schema in schemas[1:]:
        common_schema = common_schema.combine(schema, lambda s1, s2: s1 if s1 == s2 else object)

    return common_schema


def chunk_dataframe(df, chunk_size):
    """
    Chunk a dataframe into smaller dataframes.

    Args:
        df (pd.DataFrame): Dataframe to be chunked.
        chunk_size (int): Size of each chunk.

    Returns:
        list: List of chunked dataframes.
    """
    num_chunks = -(-len(df) // chunk_size)  # round up division
    return [df[i * chunk_size:(i + 1) * chunk_size] for i in range(num_chunks)]


def force_pyarrow_schema_and_save_file(df, save_path, pyarrow_schema, file_type='parquet'):
    """
    Force a dataframe to use a pyarrow schema and save it as a parquet or csv file.

    Args:
        df (pd.DataFrame): Dataframe to be saved.
        save_path (str): Path to save the file.
        pyarrow_schema (pa.schema): Pyarrow schema to be used.
        file_type (str): File type to save ('parquet' or 'csv').
    """
    df_columns = df.columns.tolist()
    schema_columns = pyarrow_schema.names

    for col in df_columns:
        if col not in schema_columns:
            df.drop(columns=col, inplace=True)

    for col in schema_columns:
        if col not in df_columns:
            df[col] = None

    for col in df.columns.tolist():
        dtype_from_df = 'string' if df[col].dtype == 'object' or df[col].dtype == 'str' else str(df[col].dtype)
        if dtype_from_df != str(pyarrow_schema.field(col).type):
            if str(pyarrow_schema.field(col).type) == 'string':
                df[col] = df[col].astype(str)
            elif 'int' in str(pyarrow_schema.field(col).type):
                df[col].fillna(0, inplace=True)
                df[col] = df[col].astype(str(pyarrow_schema.field(col).type))
            elif 'bool' in str(pyarrow_schema.field(col).type):
                df[col] = df[col].astype(bool)
            elif 'float' in str(pyarrow_schema.field(col).type):
                df[col] = df[col].astype(float)
            elif 'timestamp' in str(pyarrow_schema.field(col).type):
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True)

    df.replace(r'^None$', None, regex=True, inplace=True)
    table = pa.table(data=df, schema=pyarrow_schema)

    if file_type == 'parquet':
        pyaparquet.write_table(table=table, where=save_path)
    else:
        pyacsv.write_csv(table, save_path)


def dataframe_to_list_of_dicts(df):
    """
    Transform a dataframe to a list of dictionaries.

    Args:
        df (pd.DataFrame): Dataframe to be transformed.

    Returns:
        list: List of dictionaries.
    """
    return df.to_dict(orient='records')


def get_unique_values_on_df2(df1, df2, columns_to_compare):
    """
    Filter rows that are only in the second dataframe based on specified columns.

    Args:
        df1 (pd.DataFrame): First dataframe.
        df2 (pd.DataFrame): Second dataframe.
        columns_to_compare (list): Columns to compare.

    Returns:
        pd.DataFrame: Dataframe containing rows unique to the second dataframe.
    """
    merged_df = pd.merge(df1, df2, on=columns_to_compare, how="outer", indicator=True)
    df2_only = merged_df[merged_df['_merge'] == 'right_only'].drop(columns='_merge')
    return df2_only
