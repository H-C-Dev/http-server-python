import datetime

def show_date_time(message: str = None):
    now = datetime.datetime.now()
    print(f"{message} time: {now.strftime("%Y-%m-%d %H:%M:%S")}")

