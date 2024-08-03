import numpy as np


def split_list_to_groups_of_lists(parameter_list, max_groups=4):
    try:
        max_groups = int(max_groups)
    except:
        pass
    try:
        all_lists = []
        values_to_return = np.array_split(parameter_list, max_groups)
        for array in values_to_return:
            all_lists.append(list(array))
    except ValueError:
        group_size = len(parameter_list) // max_groups

        # Divide the list into groups
        groups = [parameter_list[i:i + group_size] for i in range(0, len(parameter_list), group_size)]
        all_lists = groups

    return all_lists
