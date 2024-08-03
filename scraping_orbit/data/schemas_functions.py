import datetime
import pyarrow as pa


def create_pyarrow_schema(column_definitions: list):
    """
    Create a PyArrow schema from a list of column definitions.

    Args:
        column_definitions (list): List of dictionaries with column names and types.
            Example: [{'column_name': int}, {'another_column': 'timestamp'}, ...]

    Returns:
        pa.Schema: PyArrow schema object.
    """
    schema_fields = []

    for column in column_definitions:
        for column_name, column_type in column.items():
            if column_type == int:
                arrow_type = pa.int32()
            elif column_type == float:
                arrow_type = pa.float32()
            elif column_type == bool:
                arrow_type = pa.bool_()
            elif column_type == str:
                arrow_type = pa.string()
            elif column_type == 'timestamp':
                arrow_type = pa.timestamp('ns')
            elif column_type == datetime.datetime:
                arrow_type = pa.timestamp('ns')
            elif column_type == datetime.date:
                arrow_type = pa.date32()
            else:
                arrow_type = pa.string()  # Default to string if type is unknown
            schema_fields.append((column_name, arrow_type))

    return pa.schema(schema_fields)
