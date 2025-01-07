import re
import unicodedata

def remove_accents(input_string):
    """
    Remove accents from a string.

    Args:
        input_string (str): The string from which to remove accents.

    Returns:
        str: The string without accents.
    """
    if "'" in input_string:
        input_string = input_string.replace("'", '')
    nfkd_form = unicodedata.normalize('NFKD', input_string)
    return ''.join([char for char in nfkd_form if not unicodedata.combining(char)])

def remove_special_characters(input_string):
    """
    Remove special characters from a string, leaving only alphanumeric characters and spaces.

    Args:
        input_string (str): The string from which to remove special characters.

    Returns:
        str: The string without special characters.
    """
    pattern = r'[^a-zA-Z0-9\s]'
    cleaned_string = re.sub(pattern, '', input_string)
    return cleaned_string
