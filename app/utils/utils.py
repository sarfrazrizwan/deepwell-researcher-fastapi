from datetime import datetime


def get_today_date_str() -> str:
    return datetime.now().strftime("%A, %B %d, %Y")
