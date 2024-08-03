import glob
import json
import logging
import multiprocessing
import threading
import os
import shutil
import time
from pathlib import Path

import pandas as pd

import scraping_orbit.utils.code_creation
from scraping_orbit.data.data_merger import merge_data_files
from scraping_orbit.utils import splitters


def execute_processes(parameters_list: list, target_function, max_workers: int, sleep_interval=2, timeout=7200):
    """
    Execute a list of processes with given parameters and target function.

    Args:
        parameters_list (list): List of parameters to be processed.
        target_function (function): The target function to be executed by the processes.
        max_workers (int): Maximum number of concurrent processes.
        sleep_interval (int, optional): Time to sleep between starting processes. Defaults to 2 seconds.
        timeout (int, optional): Timeout for joining processes. Defaults to 7200 seconds.

    """
    parameter_groups = splitters.split_list_to_groups_of_lists(parameter_list=parameters_list, max_groups=max_workers)
    processes = []
    for group in parameter_groups:
        process = multiprocessing.Process(target=target_function, args=(group,))
        processes.append(process)

    for process in processes:
        process.start()
        time.sleep(sleep_interval)

    for process in processes:
        process.join(timeout=timeout)

    for process in processes:
        process.terminate()


def execute_single_process(target_function, function_args, sleep_interval=2, timeout=7200):
    """
    Execute a single process with given target function and arguments.

    Args:
        target_function (function): The target function to be executed by the process.
        function_args (tuple): Arguments to be passed to the target function.
        sleep_interval (int, optional): Time to sleep before starting the process. Defaults to 2 seconds.
        timeout (int, optional): Timeout for joining the process. Defaults to 7200 seconds.

    """
    process = multiprocessing.Process(target=target_function, args=function_args)
    process.start()
    time.sleep(sleep_interval)
    process.join(timeout=timeout)
    process.terminate()


def execute_multiprocess_with_results(parameters_list: list,
                                      target_function,
                                      max_workers: int,
                                      result_format='json',
                                      sleep_interval=2,
                                      timeout=7200,
                                      drop_duplicates=False,
                                      duplicates_column='',
                                      keep='first',
                                      csv_delimiter=',',
                                      csv_encoding='utf8',
                                      clean_up=False,
                                      merge_method='dataframe',
                                      use_threads=False):
    """
    Execute multiple processes with results merged at the end.

    Args:
        parameters_list (list): List of parameters to be processed.
        target_function (function): The target function to be executed by the processes.
        max_workers (int): Maximum number of concurrent processes.
        result_format (str, optional): Format of the result files. Defaults to 'json'.
        sleep_interval (int, optional): Time to sleep between starting processes. Defaults to 2 seconds.
        timeout (int, optional): Timeout for joining processes. Defaults to 7200 seconds.
        drop_duplicates (bool, optional): Flag to drop duplicates in the merged results. Defaults to False.
        duplicates_column (str, optional): Column name for identifying duplicates. Defaults to ''.
        keep (str, optional): Which duplicates to keep. Defaults to 'first'.
        csv_delimiter (str, optional): Delimiter for CSV files. Defaults to ','.
        csv_encoding (str, optional): Encoding for CSV files. Defaults to 'utf8'.
        clean_up (bool, optional): Flag to remove local files after processing. Defaults to False.
        merge_method (str, optional): Method for merging results. Defaults to 'dataframe'.
        use_threads (bool, optional): Flag to use threading instead of multiprocessing. Defaults to False.

    Returns:
        DataFrame or dict or list: Merged results from the processes.

    """
    folder_code = f"temp_mp_process_{scraping_orbit.utils.code_creation.create_new_date_collected_code()}_" \
                  f"{scraping_orbit.utils.code_creation.create_random_code(max_index=4)}"
    output_dir = Path(__file__).resolve().parent / 'generated_outputs' / folder_code
    output_dir.mkdir(parents=True, exist_ok=True)
    save_dir = str(output_dir)

    parameter_groups = splitters.split_list_to_groups_of_lists(parameter_list=parameters_list, max_groups=max_workers)
    processes = []

    for group in parameter_groups:
        if use_threads:
            process = threading.Thread(target=target_function, args=(group, save_dir))
        else:
            process = multiprocessing.Process(target=target_function, args=(group, save_dir))
        processes.append(process)

    for process in processes:
        process.start()
        time.sleep(sleep_interval)

    for process in processes:
        process.join(timeout=timeout)

    for process in processes:
        process.terminate()

    logging.info('Waiting for processes to finish.')
    time.sleep(5)

    downloaded_files = glob.glob(f"{save_dir}/*")
    logging.info(f'[MP-F] Files found from the process: {len(downloaded_files)}')

    if not downloaded_files:
        logging.info('[MP-F] No files to concatenate.')
        if clean_up:
            shutil.rmtree(save_dir)
        return None

    logging.info('[MP-F] Merging results ...')

    if merge_method == 'not_dataframe' and result_format == 'json':
        merged_data = merge_json_files(downloaded_files, clean_up)
    else:
        merged_data = merge_data_files(
            file_list=downloaded_files,
            file_extension=result_format,
            drop_duplicates=drop_duplicates,
            drop_duplicates_column=duplicates_column,
            keep_duplicates=keep,
            delimiter=csv_delimiter,
            encoding=csv_encoding,
            delete_local_files=clean_up
        )

    if clean_up:
        shutil.rmtree(save_dir)

    return merged_data


def merge_json_files(files, clean_up=False):
    """
    Merge JSON files into a single dictionary or list.

    Args:
        files (list): List of file paths to be merged.
        clean_up (bool, optional): Flag to remove local files after merging. Defaults to False.

    Returns:
        dict or list: Merged content from JSON files.

    """
    merged_dict = {}
    merged_list = []
    use_list = False

    for file in files:
        try:
            with open(file, 'r') as f:
                content = json.load(f)
                if 'process_results_list' in content:
                    use_list = True
                if use_list:
                    merged_list.append(content['process_results_list'])
                else:
                    merged_dict.update(content)
            if clean_up:
                os.remove(file)
        except Exception as e:
            logging.error(f'[MP-F] Error merging JSON file {file}: {e}')

    return merged_list if use_list else merged_dict


def example_multiprocess_with_results():
    """
    Example function to demonstrate the use of execute_multiprocess_with_results.
    """
    results = execute_multiprocess_with_results(
        parameters_list=[{'arg1': 4545454}, {'arg1': 555555}],
        target_function=example_target_function,
        max_workers=2,
        result_format='parquet',
        sleep_interval=2,
        timeout=20,
        clean_up=True
    )

    print(results)
    print(type(results))


def example_target_function(parameters_list, output_dir):
    """
    Example target function for multiprocessing.

    Args:
        parameters_list (list): List of parameters for processing.
        output_dir (str): Directory to save the results.

    """
    results = []
    for parameter in parameters_list:
        random_code = scraping_orbit.utils.code_creation.create_random_code(max_index=2)
        results.append({'arg_number_received': parameter['arg1'], 'some_processed_value': random_code})

    df = pd.DataFrame(results)
    df.to_parquet(f"{output_dir}/{scraping_orbit.utils.code_creation.create_random_code()}.parquet")


if __name__ == '__main__':
    example_multiprocess_with_results()
