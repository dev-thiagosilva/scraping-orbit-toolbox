import datetime
import hashlib
import random


def create_date_collected_code():
    """
    Create a code representing the current date.

    Returns:
        str: Code representing the current date in the format 'day_month_year'.
    """
    current_date = datetime.date.today()
    return f"{current_date.day}_{current_date.month}_{current_date.year}"


def create_random_code(length=6):
    """
    Create a random numeric code.

    Args:
        length (int): Number of random numbers to generate and concatenate.

    Returns:
        str: Random numeric code.
    """
    return ''.join(str(random.randint(1, 99999)) for _ in range(length))


def create_month_year_period():
    """
    Create a code representing the current month and year.

    Returns:
        str: Code representing the current month and year in the format 'month_year'.
    """
    current_date = datetime.date.today()
    return f"{current_date.month}_{current_date.year}"


def create_random_file_name():
    """
    Create a random file name based on the current date and a random code.

    Returns:
        str: Random file name in the format 'day_month_year_randomcode'.
    """
    date_code = create_date_collected_code()
    random_code = create_random_code(length=10)
    return f"{date_code}_{random_code}"


def create_custom_hashid(input_string):
    """
    Create a hash ID from the input string using MD5 algorithm and UTF-8 encoding.

    Args:
        input_string (str): String to hash.

    Returns:
        str: Hash ID of the string.
    """
    return hashlib.md5(input_string.encode("utf-8")).hexdigest()
