from datetime import datetime
def calculate_duration_minutes(start_time, end_time):
    try:
        sh, sm = map(int, start_time.split(':'))
        eh, em = map(int, end_time.split(':'))
        return (eh * 60 + em) - (sh * 60 + sm)
    except:
        return 60
