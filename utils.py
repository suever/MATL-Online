from datetime import datetime


def parse_iso8601(date):
    """
    Convert a date in ISO 8601 format (used by github) to a datetime object
    """
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
