import datetime
import glob
import json
import multiprocessing
import os
import shutil
import time  # Library for handling time-related operations
import traceback
from pathlib import Path

import GPUtil  # GPU monitoring library
import cv2
import matplotlib.pyplot as plt
import pandas as pd
import psutil  # Library for system monitoring
import platform
from scraping_toolkit.utils import code_creation


def check_os():
    # Get the current OS name
    os_name = platform.system()

    # Check if it's Linux or Windows
    if os_name.lower() == 'linux':
        return "Linux"
    elif os_name.lower() == 'windows':
        return "Windows"
    else:
        return "Unknown"


def start_monitoring():
    return __get_last_tracking()


def end_monitoring(initial_tracking, return_image=False):
    if initial_tracking is None:
        pass
    else:
        try:
            current_path = Path(__file__).resolve().parent.joinpath('temp_performance_tracking')
            current_path.mkdir(parents=True, exist_ok=True)

            actual_tracking = __get_last_tracking()

            if return_image:
                file_image = f"{current_path}/performance_image.png"
                img = cv2.imread(file_image)
            else:
                img = None

            def get_creation_time(filepath):
                return os.path.getctime(filepath)

            def get_files_between(file1, file2, directory):
                # Obter as datas de criação dos arquivos
                creation_time1 = get_creation_time(file1)
                creation_time2 = get_creation_time(file2)

                # Determinar a faixa de datas
                start_time = min(creation_time1, creation_time2)
                end_time = max(creation_time1, creation_time2)

                # Obter todos os arquivos no diretório especificado
                all_files = [os.path.join(directory, f) for f in os.listdir(directory) if
                             os.path.isfile(os.path.join(directory, f))]

                # Filtrar arquivos que foram criados dentro da faixa de datas
                files_between = [f for f in all_files if start_time <= get_creation_time(f) <= end_time]

                return files_between

            def processa_dados(lista_de_dicionarios):
                # Ordena a lista de dicionários pela chave 'date_time'
                lista_ordenada = sorted(lista_de_dicionarios, key=lambda x: x['date_time'])

                # Inicializa um dicionário para armazenar os resultados
                resultado = {
                    "CPU Usage (%)": [],
                    "Used Cores": [],
                    "Memory Usage (GB)": [],
                    "Memory Usage (%)": [],
                    "GPU Usage (GB)": [],
                    "GPU Usage (%)": [],
                    "total_disk_size": []
                }

                # Itera sobre as chaves relevantes
                for chave in resultado.keys():
                    valores = [d[chave] for d in lista_ordenada]

                    # Calcula o valor mínimo, máximo e médio
                    min_valor = min(valores)
                    max_valor = max(valores)
                    media_valor = sum(valores) / len(valores)

                    # Calcula o percentual de aumento entre o valor médio e o valor máximo
                    percentual_aumento = ((media_valor - min_valor) / min_valor) * 100 if min_valor != 0 else 0

                    # Calcula o valor de uso (média - primeiro valor)
                    valor_uso = media_valor - min_valor
                    resultado[chave] = {
                        'usage_min': min_valor,
                        'usage_max': max_valor,
                        'usage_avg': media_valor,
                        'increase_percent': percentual_aumento,
                        'total_usage': valor_uso,
                    }

                    # Adiciona os resultados ao dicionário de resultado

                return resultado

            directory = str(Path(__file__).resolve().parent.joinpath('temp_performance_tracking'))
            files_between = get_files_between(file1=initial_tracking['file'],
                                              file2=actual_tracking['file'],
                                              directory=directory)

            dict_files = []
            for file in files_between:
                with open(str(file), 'r') as openfile:
                    dict_file = json.load(openfile)
                    dict_files.append(dict_file)

            if len(dict_files) != 0:
                result = processa_dados(lista_de_dicionarios=dict_files)
                if return_image:
                    return result, img
                else:
                    return result
            else:
                if return_image:
                    return None, None
                else:
                    return None
        except:
            print(traceback.format_exc())
            if return_image:

                return None, None
            else:
                return None


def _maintain_recent_files(path_pattern, max_files=800):
    # Use glob to find files matching the path pattern
    files = glob.glob(path_pattern)

    # Get the modification time for each file
    files_with_mtime = [(file, os.path.getmtime(file)) for file in files]

    # Sort files by modification time (most recent first)
    files_with_mtime.sort(key=lambda x: x[1], reverse=True)

    # Keep only the max_files most recent files
    files_to_keep = files_with_mtime[:max_files]
    files_to_delete = files_with_mtime[max_files:]

    # Delete files that are not in the recent files list
    for file, mtime in files_to_delete:
        try:
            os.remove(file)

        except Exception as e:
            pass


def __mp_initialize_system_monitoring(log_status):
    current_path = Path(__file__).resolve().parent.joinpath('temp_performance_tracking')
    current_path.mkdir(parents=True, exist_ok=True)
    print('System monitoring initialized.')

    def create_usage_chart(cpu_data: list, memory_data: list, gpu_data: list) -> plt:
        # Create a chart with the latest data
        plt.figure(figsize=(10, 6))

        # Set the background color to black
        plt.gca().set_facecolor('black')

        # Plot CPU Usage
        plt.plot(cpu_data, label='CPU Usage (%)', color='green')

        # Plot Memory Usage
        plt.plot(memory_data, label='Memory Usage (%)', color='blue')

        # Plot GPU Usage
        plt.plot(gpu_data, label='GPU Usage (%)', color='orange')

        # Set y-axis range between 0 and 100
        plt.ylim(0, 100)

        # Set labels and title
        plt.xlabel('Time')
        plt.ylabel('Percentage')
        plt.title('CPU, Memory, and GPU Usage')

        # Get the legend frame and set face color for the legend
        legend = plt.legend()
        legend.get_frame().set_facecolor('black')

        # Get the legend texts and set color
        for text in legend.get_texts():
            text.set_color('white')

        # Set the background color of the entire plot
        plt.gca().set_facecolor('black')

        return plt

    # Define a function to check system conditions
    def check_system_conditions(log_status) -> dict:
        # Get CPU usage for each core
        cpu_percent = psutil.cpu_percent()
        cpu_percent_per_core = psutil.cpu_percent(percpu=True)
        used_cores = sum(1 for percent in cpu_percent_per_core if percent > 0)

        # Get memory information
        memory_info = psutil.virtual_memory()
        memory_used_gb = memory_info.used / (1024 ** 3)  # Convert bytes to GB
        memory_percent = memory_info.percent

        # Get GPU information
        gpu_info = GPUtil.getGPUs()[0]
        gpu_percent = gpu_info.load * 100  # GPU usage in percentage
        gpu_memory_used_gb = (gpu_info.memoryTotal * (gpu_percent / 100)) / 1000  # GPU memory used in GB

        # Collect data in a dictionary
        result: dict = {
            'CPU Usage (%)': cpu_percent,
            'Used Cores': used_cores,
            'Memory Usage (GB)': memory_used_gb,
            'Memory Usage (%)': memory_percent,
            'GPU Usage (GB)': float(gpu_memory_used_gb),
            'GPU Usage (%)': gpu_percent
        }
        if log_status:
            # Print the information
            print(f"System Conditions:\n"
                  f"  CPU Usage (%): {result['CPU Usage (%)']} |"
                  f"  Used Cores: {result['Used Cores']} |"
                  f"  Memory Usage (GB): {result['Memory Usage (GB)']:.2f} GB |"
                  f"  Memory Usage (%): {result['Memory Usage (%)']}% |"
                  f"  GPU Usage (GB): {result['GPU Usage (GB)']:.2f} GB |"
                  f"  GPU Usage (%): {result['GPU Usage (%)']}%")

        return result

    def get_total_disk_size_in_gb(path="/"):
        """
        Returns the total size of the disk in GB as a float.

        :param path: Path to check. Defaults to "/" for the entire disk.
        :return: Total size of the disk in GB as a float.
        """
        total, _, _ = shutil.disk_usage(path)
        total_gb = total / (1024 ** 3)  # Convert bytes to GB
        return total_gb

    # Example usage
    total_size_gb = get_total_disk_size_in_gb()
    print(f"Total Disk Size: {total_size_gb:.2f} GB")

    # Formatting the output to show MB instead of GB when appropriate
    def format_output(value, unit="GB"):
        """
        Formats the input value according to the specified unit.

        :param value: Input value in GB.
        :param unit: Unit to display ('GB', 'MB').
        :return: Formatted string representing the size.
        """
        if unit.lower() == "gb":
            return float(f"{value:.2f}")
        elif unit.lower() == "mb":
            return float(f"{value * 1024:.2f}")
        else:
            return 0

    # Initial placeholder dictionaries for each variable
    cpu_usage_dict: dict = {'CPU Usage (%)': 0}
    used_cores_dict: dict = {'Used Cores': 0}
    memory_usage_gb_dict: dict = {'Memory Usage (GB)': 0}
    memory_usage_percent_dict: dict = {'Memory Usage (%)': 0}
    gpu_usage_gb_dict: dict = {'GPU Usage (GB)': 0}
    gpu_usage_percent_dict: dict = {'GPU Usage (%)': 0}

    # Lists to store historical data for chart plotting
    memory_usage_gb_data: list = []
    gpu_usage_gb_data: list = []
    cpu_usage_data: list = []

    # Infinite loop to continuously update and display system conditions
    while True:
        # Get system conditions
        current_conditions = check_system_conditions(log_status)
        now = datetime.datetime.now()  # current date and time
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        time_now = now.strftime("%H:%M:%S.%f")[:-4]
        timestring = now.strftime("%H_%M_%S_%f")[:-4]
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S.%f")[:-4]

        # Update the dictionaries with new values
        cpu_usage_dict['CPU Usage (%)'] = current_conditions['CPU Usage (%)']
        used_cores_dict['Used Cores'] = current_conditions['Used Cores']
        memory_usage_gb_dict['Memory Usage (GB)'] = current_conditions['Memory Usage (GB)']
        memory_usage_percent_dict['Memory Usage (%)'] = current_conditions['Memory Usage (%)']
        gpu_usage_gb_dict['GPU Usage (GB)'] = current_conditions['GPU Usage (GB)']
        gpu_usage_percent_dict['GPU Usage (%)'] = current_conditions['GPU Usage (%)']
        file_name = f"{current_path}/{timestring}___{code_creation.create_random_code(max_index=4)}.json"
        formatted_size = format_output(total_size_gb, unit="GB")  # Defaulting to GB
        final_dict = {
            'CPU Usage (%)': current_conditions['CPU Usage (%)'],
            'Used Cores': current_conditions['Used Cores'],
            'Memory Usage (GB)': current_conditions['Memory Usage (GB)'],
            'Memory Usage (%)': current_conditions['Memory Usage (%)'],
            'GPU Usage (GB)': current_conditions['GPU Usage (GB)'],
            'GPU Usage (%)': current_conditions['GPU Usage (%)'],
            'date_time': date_time,
            'time': time_now,
            'file': file_name,
            'total_disk_size': formatted_size,

        }

        # Update the chart with the latest data
        memory_usage_gb_data.append(memory_usage_percent_dict['Memory Usage (%)'])
        gpu_usage_gb_data.append(gpu_usage_percent_dict['GPU Usage (%)'])
        cpu_usage_data.append(cpu_usage_dict['CPU Usage (%)'])

        memory_usage_gb_data = memory_usage_gb_data[-100:]
        gpu_usage_gb_data = gpu_usage_gb_data[-100:]
        cpu_usage_data = cpu_usage_data[-100:]

        chart_data = pd.DataFrame({
            'Memory Usage %': memory_usage_gb_data,
            'GPU Usage %': gpu_usage_gb_data,
            'CPU Usage %': cpu_usage_data
        })

        cpu_usage_data.append(current_conditions['CPU Usage (%)'])
        memory_usage_gb_data.append(current_conditions['Memory Usage (%)'])
        gpu_usage_gb_data.append(current_conditions['GPU Usage (%)'])

        # Keep only the last 100 data points
        cpu_usage_data = cpu_usage_data[-100:]
        memory_usage_gb_data = memory_usage_gb_data[-100:]
        gpu_usage_gb_data = gpu_usage_gb_data[-100:]

        # Create the chart
        chart = create_usage_chart(cpu_usage_data, memory_usage_gb_data, gpu_usage_gb_data)

        file_image = f"{current_path}/performance_image.png"
        final_dict['graphic'] = file_image
        chart.savefig(file_image)
        json_object = json.dumps(final_dict, indent=4)
        with open(file_name, "w") as outfile:
            outfile.write(json_object)

        # Add a short sleep to prevent excessive updates
        time.sleep(0.3)


def mp_maintain_files():
    current_path = Path(__file__).resolve().parent.joinpath('temp_performance_tracking')
    current_path.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            _maintain_recent_files(path_pattern=f"{current_path}/*.json",
                                   max_files=15000)
            time.sleep(10)

        except:
            time.sleep(10)
            pass


def reinitialize_system_monitoring(log_status=False):
    current_path = Path(__file__).resolve().parent.joinpath('temp_performance_tracking')
    current_path.mkdir(parents=True, exist_ok=True)
    # Define the path to the lock file
    lock_file_path = f"{str(current_path)}/my_process.lock"

    if os.path.exists(lock_file_path):
        os.remove(lock_file_path)
    open(lock_file_path, 'a').close()

    p = multiprocessing.Process(target=__mp_initialize_system_monitoring,
                                args=(log_status,))
    p.start()

    p2 = multiprocessing.Process(target=mp_maintain_files,
                                 args=())
    p2.start()

    time.sleep(2)
    return p

def initialize_system_monitoring(log_status=False):
    current_path = Path(__file__).resolve().parent.joinpath('temp_performance_tracking')
    current_path.mkdir(parents=True, exist_ok=True)
    # Define the path to the lock file
    lock_file_path = f"{str(current_path)}/my_process.lock"
    if os.path.exists(lock_file_path):
        print("Process is already running or was not terminated properly last time.")
        return None
    else:
        # Create the lock file indicating the process has started
        open(lock_file_path, 'a').close()

        p = multiprocessing.Process(target=__mp_initialize_system_monitoring,
                                    args=(log_status,))
        p.start()

        p2 = multiprocessing.Process(target=mp_maintain_files,
                                     args=())
        p2.start()

        time.sleep(2)
        return p


def __get_last_tracking():
    current_path = Path(__file__).resolve().parent.joinpath('temp_performance_tracking')
    current_path.mkdir(parents=True, exist_ok=True)

    path_pattern = f"{current_path}/*.json"
    files = glob.glob(path_pattern)

    try:
        # Keep only the max_files most recent files
        try:
            # Get the modification time for each file
            files_with_mtime = [(file, os.path.getmtime(file)) for file in files]

            # Sort files by modification time (most recent first)
            files_with_mtime.sort(key=lambda x: x[1], reverse=True)

            selected_file = files_with_mtime[:100][0][0]
        except:
            # Get a list of all files in the directory
            files = glob.glob(os.path.join(current_path, '*.json'))

            # Create a list of tuples (filename, modification_time)
            files_with_mtime = [(file, os.path.getmtime(file)) for file in files]

            # Sort the files by modification time in descending order
            files_with_mtime.sort(key=lambda x: x[1], reverse=True)
            # Select the most recently modified file among the top 100 files
            selected_file = files_with_mtime[:100][0][0]
        with open(str(selected_file), 'r') as openfile:
            dict_file = json.load(openfile)
            return dict_file
    except:
        print(traceback.format_exc())
        return None


if __name__ == '__main__':
    initialize_system_monitoring()
    result = start_monitoring()
    print(result)
    end, image = end_monitoring(initial_tracking=result,
                                return_image=True)
    print(end)
