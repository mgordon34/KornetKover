from datetime import datetime

def get_nba_year_from_date(date: datetime.date) -> str:
    date = date_to_str(date)
    cutoff_month = 10
    date_split = date.split("-")

    if int(date_split[1]) < cutoff_month:
        return str(int(date_split[0]) - 1)
    return date_split[0]

def date_to_str(date: datetime.date) -> str:
    return date.strftime("%Y-%m-%d")

def str_to_date(date: str) -> datetime.date:
    return datetime.strptime(date, "%Y-%m-%d")