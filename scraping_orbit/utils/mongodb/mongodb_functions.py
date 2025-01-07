import datetime
import hashlib
import traceback
import pymongo
from pymongo.errors import ConnectionFailure, DuplicateKeyError


def create_mongodb_connection(host: str, username: str, password: str,
                              drivername: str = 'drivername',
                              port: str = 'port'):
    """
    Create a MongoDB connection.

    Args:
        host (str): MongoDB host.
        username (str): MongoDB username.
        password (str): MongoDB password.

    Returns:
        pymongo.MongoClient or bool: MongoDB client instance if connection is successful, otherwise False.
        :param password:
        :param username:
        :param host:
        :param drivername:
        :param port:
    """
    config = {
        "drivername": drivername,
        "host": host,
        "port": port,
        "username": username,
        "password": password
    }

    if host == 'localhost':
        if not username:
            url = f'{config["drivername"]}://{config["host"]}:{config["port"]}/?authSource=admin'
        else:
            url = f'{config["drivername"]}://{config["username"]}:{config["password"]}@{config["host"]}:{config["port"]}/?authSource=admin'
    else:
        url = f'{config["drivername"]}://{config["username"]}:{config["password"]}@{config["host"]}:{config["port"]}/?authSource=admin'

    client = pymongo.MongoClient(url)

    try:
        client.admin.command('ismaster')
        return client
    except ConnectionFailure:
        print("MongoDB Server not available")
        return False


def insert_into_mongodb(client, database_name: str, collection_name: str, data: dict):
    """
    Insert a document into a MongoDB collection.

    Args:
        client (pymongo.MongoClient): MongoDB client instance.
        database_name (str): Name of the database.
        collection_name (str): Name of the collection.
        data (dict): Document to insert.

    Returns:
        bool: True if insert is successful, otherwise False.
    """
    try:
        db = client[database_name]
        collection = db[collection_name]
        collection.insert_one(data)
        return True
    except Exception:
        print(traceback.format_exc())
        return False


def remove_value_mongodb(client, database_name: str, collection_name: str, query: dict):
    """
    Remove documents from a MongoDB collection.

    Args:
        client (pymongo.MongoClient): MongoDB client instance.
        database_name (str): Name of the database.
        collection_name (str): Name of the collection.
        query (dict): Query to match documents to remove.

    Returns:
        bool: True if removal is successful, otherwise False.
    """
    try:
        db = client[database_name]
        collection = db[collection_name]
        collection.delete_many(query)
        return True
    except Exception:
        print(traceback.format_exc())
        return False


def close_mongodb_connection(client):
    """
    Close MongoDB connection.

    Args:
        client (pymongo.MongoClient): MongoDB client instance.
    """
    try:
        client.close()
    except Exception:
        print(traceback.format_exc())


def create_mongo_index(client, database_name: str, collection_name: str, index_value: str, log_status=False,
                       close_connection=False):
    """
    Create an index in a MongoDB collection for deduplication.

    Args:
        client (pymongo.MongoClient): MongoDB client instance.
        database_name (str): Name of the database.
        collection_name (str): Name of the collection.
        index_value (str): Value to insert as index.
        log_status (bool): Log status of index creation.
        close_connection (bool): Close MongoDB connection after operation.

    Returns:
        bool: True if index creation is successful, otherwise False.
    """
    import logging
    db = client[database_name]
    collection = db[collection_name]
    index_field = 'hash_index'

    try:
        collection.insert_one({index_field: index_value})
        if log_status:
            logging.info("Inserted one value to index")
        collection.create_index([(index_field, pymongo.DESCENDING)], unique=True)

        if close_connection:
            client.close()
        return True
    except DuplicateKeyError:
        if log_status:
            logging.info("Index already present")
        return False


def deduplication_verification(index_value: str, client, database_name='applications_database',
                               collection_name='deduplication_process'):
    """
    Verify deduplication in MongoDB.

    Args:
        index_value (str): Value to index.
        client (pymongo.MongoClient): MongoDB client instance.
        database_name (str): Name of the database.
        collection_name (str): Name of the collection.

    Returns:
        bool: True if index is not present, otherwise False.
    """
    try:
        hash_id = create_custom_hashid(index_value)
        index_created = create_mongo_index(client, database_name, collection_name, hash_id, log_status=False)
        return index_created
    except Exception:
        print(traceback.format_exc())
        return True


def remove_value_from_deduplication(index_value: str, client, database_name='applications_database',
                                    collection_name='deduplication_process'):
    """
    Remove deduplication value from MongoDB collection.

    Args:
        index_value (str): Value to index.
        client (pymongo.MongoClient): MongoDB client instance.
        database_name (str): Name of the database.
        collection_name (str): Name of the collection.

    Returns:
        bool: True if removal is successful, otherwise False.
    """
    try:
        hash_id = create_custom_hashid(index_value)
        removed = remove_value_mongodb(client, database_name, collection_name, {'hash_index': hash_id})
        return removed
    except Exception:
        print(traceback.format_exc())
        return True


def create_custom_hashid(string_hashcode: str):
    """
    Create a hash id from the input string using MD5 algorithm and UTF-8 encoding.

    Args:
        string_hashcode (str): String to hash.

    Returns:
        str: Hash ID of the string.
    """
    return hashlib.md5(string_hashcode.encode("utf-8")).hexdigest()


def create_collected_period():
    """
    Create the collected period of data.

    Returns:
        str: Period in the format 'month_year'.
    """
    current_date = datetime.date.today()
    return f"{current_date.month}_{current_date.year}"
