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


    duration = calculate_duration_minutes(task.start_time, task.end_time)
    if duration <= 30:
        duration_bonus = 5
    elif duration <= 60:
        duration_bonus = 3
    else:
        duration_bonus = 0

    days_old = (datetime.utcnow() - task.created_at).days
    age_bonus = min(days_old, 10)

    return p + urgency + duration_bonus + age_bonus

def prioritize_tasks(tasks):
    pending = [t for t in tasks if t.status != 'Done']
    pending.sort(key=lambda t: (
        -score(t),
        t.due_date or datetime.max,
        calculate_duration_minutes(t.start_time, t.end_time),
        t.created_at
    ))
    return pending


def get_todays_tasks(tasks):
    today = datetime.utcnow().date()
    pending = [t for t in tasks if t.status != 'Done']
    return [t for t in pending if t.due_date and t.due_date.date() == today]

def get_overdue_tasks(tasks):
    now = datetime.utcnow()
    return [t for t in tasks if t.status != 'Done' and t.due_date and t.due_date < now]

def get_next_task(tasks):
    prioritized = prioritize_tasks(tasks)
    return prioritized[0] if prioritized else None

