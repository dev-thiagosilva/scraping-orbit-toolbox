from datetime import date, timedelta


def get_dates_between(start_date_list: list, end_date_list: list):
    """
    Generates a list of dates between two dates (inclusive).

    Args:
        start_date_list (list): Start date in [year, month, day] format.
        end_date_list (list): End date in [year, month, day] format.

    Returns:
        list: List of date objects between the start and end dates.
    """
    try:
        start_date = date(int(start_date_list[0]), int(start_date_list[1]), int(start_date_list[2]))
        end_date = date(int(end_date_list[0]), int(end_date_list[1]), int(end_date_list[2]))
    except (ValueError, IndexError) as e:
        raise ValueError("Invalid date format. Please provide dates as [year, month, day].") from e

    if start_date > end_date:
        raise ValueError("Start date must be before or equal to end date.")

    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    return date_range
