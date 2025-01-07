import datetime
import json
import logging
import multiprocessing
import os
import re
import traceback
from pathlib import Path
from urllib.parse import urlparse

import boto3
import numpy as np
import pandas as pd

from scraping_orbit.utils.parsing.string_parsers import remove_accents as string_parsers_remove_accents
from scraping_orbit.utils.code_creation import create_random_code, \
    create_random_file_name

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


def check_aws_client(aws_key, aws_secret, aws_region):
    """Check if AWS S3 client can be initialized with provided credentials."""
    try:
        boto3.client('s3', aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=aws_region)
        return True
    except Exception:
        return False


def download_and_read_s3_file(s3_url, bucket_name, aws_key, aws_secret, aws_region):
    """
    Download a file from S3 and read its contents into a DataFrame or dictionary.

    Args:
        s3_url: S3 URL of the file.
        bucket_name: Name of the S3 bucket.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.

    Returns:
        DataFrame or dictionary containing the file data.

    Raises:
        ValueError: If the URL is not an S3 URL or the file format is unsupported.
    """
    # Parse S3 URL
    parsed_url = urlparse(s3_url)
    if parsed_url.scheme != 's3':
        raise ValueError("Prefix file must start with 's3://'.")

    # Extract file key from S3 URL
    file_key = parsed_url.path.lstrip('/')

    # Initialize Boto3 client for S3
    s3_client = boto3.client('s3', aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=aws_region)

    # Create a temporary file to store the downloaded file
    temp_file = Path(__file__).resolve().parent / 'temp_s3_folder'
    temp_file.mkdir(parents=True, exist_ok=True)
    temp_file = temp_file / f'{s3_url.split("/")[-1]}'
    print(temp_file)

    # Download the file from S3 to the temporary file
    s3_client.download_file(bucket_name, file_key, str(temp_file))

    # Determine file type and read into DataFrame or dict accordingly
    file_extension = file_key.split('.')[-1].lower()

    try:
        if file_extension == 'json':
            with open(temp_file, 'r') as f:
                data = json.load(f)
            return data
        elif file_extension in ['xlsx', 'xls', 'csv', 'parquet']:
            if file_extension == 'csv':
                df = pd.read_csv(temp_file)
            elif file_extension in ['xls', 'xlsx']:
                df = pd.read_excel(temp_file)
            elif file_extension == 'parquet':
                df = pd.read_parquet(temp_file)
            return df
        else:
            raise ValueError("Unsupported file format. Supported formats are: JSON, XLSX, XLS, CSV, and Parquet.")
    finally:
        try:
            os.remove(temp_file)
        except Exception:
            pass


def file_exists_in_s3(bucket_name: str, file_path: str, aws_key: str = None, aws_secret: str = None,
                      aws_region: str = None, aws_session=None) -> bool:
    """
    Check if a file exists in an S3 bucket.

    Args:
        bucket_name: Name of the S3 bucket.
        file_path: Path (key) of the file in the S3 bucket.
        aws_key: AWS access key ID.
        aws_secret: AWS secret access key.
        aws_region: AWS region.
        aws_session: (optional) Already created Boto3 session.

    Returns:
        True if the file exists, False otherwise.
    """
    session = aws_session or boto3.Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret,
                                           region_name=aws_region)
    s3 = session.client('s3')
    try:
        s3.head_object(Bucket=bucket_name, Key=file_path)
        return True
    except Exception:
        return False


def folder_exists_in_s3(bucket_name: str, folder_path: str, aws_key: str = None, aws_secret: str = None,
                        aws_region: str = None, aws_session=None) -> bool:
    """
    Check if a folder exists in an S3 bucket.

    Args:
        bucket_name: Name of the S3 bucket.
        folder_path: Path (prefix) of the folder in the S3 bucket.
        aws_key: AWS access key ID.
        aws_secret: AWS secret access key.
        aws_region: AWS region.
        aws_session: (optional) Already created Boto3 session.

    Returns:
        True if the folder exists, False otherwise.
    """
    session = aws_session or boto3.Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret,
                                           region_name=aws_region)
    s3 = session.client('s3')
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)
        return 'Contents' in response
    except Exception:
        return False


def upload_json_to_s3(json_object, s3_path, bucket_name, aws_key, aws_secret, aws_region):
    """
    Upload a JSON object to an S3 bucket.

    Args:
        json_object: JSON object to upload.
        s3_path: S3 path where the JSON object will be saved.
        bucket_name: Name of the S3 bucket.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.
    """
    s3_path = s3_path.rstrip('/')
    parts = s3_path.split('/')
    filename = parts[-1] if '.' in parts[-1] else ""
    s3_path = '/'.join(parts[:-1]) if filename else s3_path

    temp_file = Path(__file__).resolve().parent / 'temp_s3_folder_2'
    temp_file.mkdir(parents=True, exist_ok=True)
    temp_file = temp_file / f'{create_random_code()}.json'

    with open(temp_file, 'w') as outfile:
        json.dump(json_object, outfile)

    save_file_to_aws_s3(
        file_to_save=temp_file,
        aws_file_name=filename,
        aws_bucket_name=bucket_name,
        aws_key=aws_key,
        aws_secret=aws_secret,
        aws_region=aws_region,
        use_prefix_instead=s3_path
    )

    try:
        os.remove(temp_file)
    except Exception:
        pass


def upload_parquet_to_s3(df: pd.DataFrame, s3_path, bucket_name, aws_key, aws_secret, aws_region):
    """
    Upload a DataFrame as a Parquet file to an S3 bucket.

    Args:
        df: DataFrame to upload.
        s3_path: S3 path where the Parquet file will be saved.
        bucket_name: Name of the S3 bucket.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.
    """
    s3_path = s3_path.rstrip('/')
    parts = s3_path.split('/')
    filename = parts[-1] if '.' in parts[-1] else ""
    s3_path = '/'.join(parts[:-1]) if filename else s3_path

    temp_file = Path(__file__).resolve().parent / 'temp_s3_folder_3'
    temp_file.mkdir(parents=True, exist_ok=True)
    temp_file = temp_file / f'{create_random_code()}.parquet'

    df.to_parquet(temp_file, compression='gzip', engine='fastparquet')

    save_file_to_aws_s3(
        file_to_save=temp_file,
        aws_file_name=filename,
        aws_bucket_name=bucket_name,
        aws_key=aws_key,
        aws_secret=aws_secret,
        aws_region=aws_region,
        use_prefix_instead=s3_path
    )

    try:
        os.remove(temp_file)
    except Exception:
        pass


def discover_files_in_s3(prefix, bucket_name, aws_key, aws_secret, aws_region, aws_session=None, get_only_latest=False,
                         ignore_subtrees=False):
    """
    Discover files inside an S3 path.

    Args:
        prefix: Path prefix to search within.
        bucket_name: Name of the S3 bucket.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.
        aws_session: (optional) Already created Boto3 session.
        get_only_latest: If True, return only the latest file.
        ignore_subtrees: If True, ignore subdirectories.

    Returns:
        List of file keys.
    """
    session = aws_session or boto3.Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret,
                                           region_name=aws_region)
    s3 = session.client('s3') if get_only_latest else session.resource('s3')
    files = []

    if get_only_latest:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        try:
            all_files = response['Contents']
            latest = max(all_files, key=lambda x: x['LastModified'])
            files.append(latest['Key'])
        except Exception:
            pass
    else:
        bucket = s3.Bucket(bucket_name)
        for obj in bucket.objects.filter(Prefix=prefix):
            if ignore_subtrees and len(obj.key.split('/')) > len(prefix.split('/')) + 1:
                continue
            files.append(obj.key)

    return [file for file in files if not file.endswith("/")]


def discover_folders_in_s3(prefix, bucket_name, aws_key, aws_secret, aws_region, aws_session=None):
    """
    Discover folders inside an S3 path.

    Args:
        prefix: Path prefix to search within.
        bucket_name: Name of the S3 bucket.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.
        aws_session: (optional) Already created Boto3 session.

    Returns:
        List of folder prefixes.
    """
    session = aws_session or boto3.Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret,
                                           region_name=aws_region)
    paginator = session.client('s3').get_paginator('list_objects')
    folders = []

    for response_data in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
        folders.extend(prefix['Prefix'].rstrip('/') for prefix in response_data.get('CommonPrefixes', []))

    return folders


def discover_files_between_dates(start_date, end_date, pre_date_prefix, post_date_prefix, date_partition, bucket_name,
                                 aws_key, aws_secret, aws_region):
    """
    Discover files between two dates in an S3 path.

    Args:
        start_date: Start date (yyyy-mm-dd).
        end_date: End date (yyyy-mm-dd).
        pre_date_prefix: Prefix before date partition.
        post_date_prefix: Prefix after date partition.
        date_partition: Name of the date partition.
        bucket_name: Name of the S3 bucket.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.

    Returns:
        List of file keys.
    """
    start_date_list = start_date.split('-')
    end_date_list = end_date.split('-')

    days_selected = get_dates_between_two_dates(start_date_list, end_date_list)
    files = []

    for day in days_selected:
        prefix = f"{pre_date_prefix}/{date_partition}={day}/{post_date_prefix}".replace('//', '/')
        logging.info(f"Discovering files from {prefix}")

        discovered_files = discover_files_in_s3(prefix, bucket_name, aws_key, aws_secret, aws_region)
        files.extend(discovered_files)
        logging.info(f"{len(discovered_files)} files found in {prefix}")

    logging.info(f"{len(files)} files found between dates {days_selected}")
    return files


def remove_file_from_s3(aws_key, aws_secret, aws_region, bucket_name, file_key):
    """
    Remove a file from an S3 bucket.

    Args:
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.
        bucket_name: Name of the S3 bucket.
        file_key: Key of the file to be removed.
    """
    s3 = boto3.client('s3', aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=aws_region)
    s3.delete_object(Bucket=bucket_name, Key=file_key)
    logging.info(f"Deleted {file_key} from bucket {bucket_name}")


def save_file_to_aws_s3(file_to_save, aws_file_name, aws_bucket_name, aws_key, aws_secret, aws_region=None,
                        use_prefix_instead='', log_status=False, return_exception_bool=False, remove_accents=True):
    """
    Save a file to an S3 bucket.

    Args:
        file_to_save: Path to the local file to be uploaded.
        aws_file_name: Name of the file in S3.
        aws_bucket_name: Name of the S3 bucket.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.
        use_prefix_instead: Prefix to use instead of directory list.
        log_status: If True, log the status of the upload.
        return_exception_bool: If True, return a boolean indicating success or failure.
        remove_accents: If True, remove accents from the prefix.

    Returns:
        Tuple containing the S3 path and a boolean indicating success or failure.
    """
    try:
        file_path_to_s3 = use_prefix_instead or '/'.join(filter(None, [
            string_parsers_remove_accents(part) if remove_accents else part for part in [use_prefix_instead] if part]))
        file_path_to_s3 = f"{file_path_to_s3}/{aws_file_name}".replace('//', '/')

        session = boto3.Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=aws_region)
        s3 = session.resource('s3')
        s3.meta.client.upload_file(Filename=str(file_to_save), Bucket=aws_bucket_name, Key=file_path_to_s3)

        if log_status:
            logging.info(f'Saved file to AWS S3 > {aws_bucket_name} | {file_path_to_s3}')

        return file_path_to_s3, True
    except Exception:
        logging.error('ERROR: Cannot save file to AWS S3.')
        logging.error(traceback.format_exc())
        return "", False


def download_file_from_s3(bucket_name, s3_key, local_dir, aws_key, aws_secret, aws_region, custom_filename='',
                          file_extension='parquet', log_status=True):
    """
    Download a file from an S3 bucket.

    Args:
        bucket_name: Name of the S3 bucket.
        s3_key: Key of the file to be downloaded.
        local_dir: Local directory to save the file.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.
        custom_filename: Custom filename for the downloaded file.
        file_extension: File extension of the downloaded file.
        log_status: If True, log the status of the download.

    Returns:
        Path to the downloaded file.
    """
    if not custom_filename:
        match = re.search(r'([^\/]+)\.([a-zA-Z0-9]+)$', s3_key)
        if match:
            filename = f"{match.group(1)}_{create_random_code(max_index=10)}.{match.group(2)}".replace('..', '.')
        else:
            filename = f"{create_random_file_name()}.{file_extension}".replace('..', '.')
    else:
        filename = custom_filename

    local_path = f"{local_dir}/{filename}".replace('//', '/')

    try:
        s3 = boto3.client('s3', aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=aws_region)
        s3.download_file(bucket_name, s3_key, local_path)

        if log_status:
            logging.info(f"Saved {s3_key} to {local_path}")

        return local_path
    except Exception:
        logging.error(f"Error occurred saving {s3_key} to {local_path}")
        logging.error(traceback.format_exc())
        return None


def download_files_from_s3(aws_key, aws_secret, bucket_name, prefixes, save_path, file_extension=".parquet",
                           region='us-west-2', max_workers=32, log_status=True, timeout=7200):
    """
    Download multiple files from S3 in parallel.

    Args:
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        bucket_name: Name of the S3 bucket.
        prefixes: List of prefixes to download.
        save_path: Local directory to save the files.
        file_extension: File extension of the downloaded files.
        region: AWS region.
        max_workers: Maximum number of parallel workers.
        log_status: If True, log the status of the download.
        timeout: Maximum timeout for the download process.

    Returns:
        List of paths to the downloaded files.
    """
    groups = np.array_split(prefixes, max_workers)
    processes = []

    for i in range(max_workers):
        process = multiprocessing.Process(target=_mp_download_files, args=(
        bucket_name, groups[i], save_path, aws_key, aws_secret, region, '', file_extension, log_status))
        processes.append(process)

    for process in processes:
        process.start()

    for process in processes:
        process.join(timeout=timeout)
        process.terminate()

    return [str(save_path / f'{prefix.split("/")[-1]}') for prefix in prefixes]


def _mp_download_files(bucket_name, prefixes, save_path, aws_key, aws_secret, region, custom_filename, file_extension,
                       log_status):
    """
    Multiprocessing helper function to download files from S3.

    Args:
        bucket_name: Name of the S3 bucket.
        prefixes: List of prefixes to download.
        save_path: Local directory to save the files.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        region: AWS region.
        custom_filename: Custom filename for the downloaded files.
        file_extension: File extension of the downloaded files.
        log_status: If True, log the status of the download.
    """
    for prefix in prefixes:
        download_file_from_s3(bucket_name, prefix, save_path, aws_key, aws_secret, region, custom_filename,
                              file_extension, log_status)


def create_s3_session(aws_key, aws_secret, bucket_name, region='us-west-2'):
    """
    Create a Boto3 session for an S3 bucket.

    Args:
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        bucket_name: Name of the S3 bucket.
        region: AWS region.

    Returns:
        S3 bucket client.
    """
    session = boto3.Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region)
    s3 = session.resource('s3')
    return s3.Bucket(bucket_name)


def create_boto3_client(aws_key, aws_secret, region='us-west-2'):
    """
    Create a Boto3 client.

    Args:
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        region: AWS region.

    Returns:
        Boto3 session.
    """
    return boto3.Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region)


def get_dates_between_two_dates(start_date_list, end_date_list):
    """
    Get a list of dates between two dates.

    Args:
        start_date_list: List containing the start date [year, month, day].
        end_date_list: List containing the end date [year, month, day].

    Returns:
        List of dates between the start and end dates.
    """
    start_date = datetime.date(int(start_date_list[0]), int(start_date_list[1]), int(start_date_list[2]))
    end_date = datetime.date(int(end_date_list[0]), int(end_date_list[1]), int(end_date_list[2]))

    delta = end_date - start_date
    return [start_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]


def s3_download_between_dates(start_date, end_date, pre_date_prefix, post_date_prefix, date_partition, bucket_name,
                              aws_key, aws_secret, aws_region, local_path, file_extension, max_workers, is_parallel,
                              max_parallel, parallel_number):
    """
    Download files between date prefixes from S3.

    Args:
        start_date: Start date string (yyyy-mm-dd).
        end_date: End date string (yyyy-mm-dd).
        pre_date_prefix: Prefix before date partition.
        post_date_prefix: Prefix after date partition.
        date_partition: Name of the date partition.
        bucket_name: Name of the S3 bucket.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.
        local_path: Local path to save downloaded files.
        file_extension: File extension of the downloaded files.
        max_workers: Maximum number of parallel workers.
        is_parallel: If True, the process is parallelized.
        max_parallel: Maximum number of parallel main processes.
        parallel_number: Number of the current parallel main process.

    Returns:
        True if successful.
    """
    start_date_list = start_date.split('-')
    end_date_list = end_date.split('-')

    days_selected = get_dates_between_two_dates(start_date_list, end_date_list)
    files = []

    for day in days_selected:
        prefix = f"{pre_date_prefix}/{date_partition}={day}/{post_date_prefix}".replace('//', '/')
        logging.info(f"Discovering files from {prefix}")

        discovered_files = discover_files_in_s3(prefix, bucket_name, aws_key, aws_secret, aws_region)
        files.extend(discovered_files)
        logging.info(f"{len(discovered_files)} files found in {prefix}")

    logging.info(f"{len(files)} files found between dates {days_selected}")

    if is_parallel:
        current_slice = parallel_number
        groups = np.array_split(files, max_parallel)
        selected_group = groups[current_slice]

        download_files_from_s3(aws_key, aws_secret, bucket_name, selected_group, local_path, file_extension, aws_region,
                               max_workers, log_status=True)
    else:
        download_files_from_s3(aws_key, aws_secret, bucket_name, files, local_path, file_extension, aws_region,
                               max_workers, log_status=True)

    return True


def find_filename_and_extension(s3_prefix):
    """
    Find the filename and extension from an S3 prefix.

    Args:
        s3_prefix: S3 prefix.

    Returns:
        Tuple containing the filename, extension, and both combined.
    """
    match = re.search(r'([^\/]+)\.([a-zA-Z0-9]+)$', s3_prefix)
    if match:
        filename = match.group(1)
        extension = match.group(2)
        return filename, extension, f"{filename}.{extension}".replace('..', '.')
    else:
        return None, None, None


def split_list_into_groups(lst, max_groups=4):
    """
    Split a list into a specified number of groups.

    Args:
        lst: List to be split.
        max_groups: Maximum number of groups.

    Returns:
        List of lists, each containing a portion of the original list.
    """
    return [list(group) for group in np.array_split(lst, max_groups)]


def mp_quick_read_paths(group, mp_number, bucket_name, aws_key, aws_secret, aws_region):
    """
    Multiprocessing helper function to quickly read paths in S3.

    Args:
        group: List of folder prefixes.
        mp_number: Multiprocessing number.
        bucket_name: Name of the S3 bucket.
        aws_key: AWS access key.
        aws_secret: AWS secret key.
        aws_region: AWS region.
    """
    files = []

    for folder in group:
        logging.info(f"Reading folder: {folder} in bucket: {bucket_name}")
        discovered_files = discover_files_in_s3(folder, bucket_name, aws_key, aws_secret, aws_region)
        logging.info(f"Found {len(discovered_files)} files in {folder}")
        files.extend(discovered_files)

    filename = f'mp_parameter_reader_{mp_number}.parquet'
    df = pd.DataFrame({'file': files})
    df.to_parquet(filename)
