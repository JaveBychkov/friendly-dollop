from datetime import datetime

def convert_date(input_formats, value):
    """Tries to convert date string using multiple input_formats

    Parameters
    ----------
    input_formats : list
        List of date formats that should be used in converting.
    value : str
        Date string that should be converted.

    Returns
    -------
    datetime.date or None

    Examples
    -------
    >>> convert_date(['%Y-%m-%d', '%d-%m-%Y'], '1995-07-04')
    datetime.date(1995, 7, 4)
    >>> convert_date(['%Y-%m-%d', '%d-%m-%Y'], '07-1995-04')

    """
    for f in input_formats:
        try:
            return datetime.strptime(value, f).date()
        except ValueError:
            continue
    return None
