from datetime import datetime
def calculate_duration_minutes(start_time, end_time):
    try:
        sh, sm = map(int, start_time.split(':'))
        eh, em = map(int, end_time.split(':'))
        return (eh * 60 + em) - (sh * 60 + sm)
    except:
        return 60
    
def score(task):
    priority_weight = {'High': 30, 'Medium': 20, 'Low': 10}
    p = priority_weight.get(task.priority, 10)

    urgency = 0

    if task.due_date:
        hours_left = (task.due_date - datetime.utcnow()).total_seconds() / 3600
        if hours_left < 0:
            urgency = 50
        elif hours_left < 24:
            urgency = 40
        elif hours_left < 48:
            urgency = 30
        elif hours_left < 168:
            urgency = 15
        else:
            urgency = 5
