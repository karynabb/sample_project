from datetime import datetime


def convert_str_to_date(date: str) -> datetime:
    return datetime.strptime(date, "%Y-%m-%d")
