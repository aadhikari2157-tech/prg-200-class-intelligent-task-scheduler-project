from datetime import datetime, timedelta

NPT_OFFSET = timedelta(hours=5, minutes=45)

def now_npt():
    """Returns the current time adjusted to Nepal Standard Time"""
    return datetime.utcnow() + NPT_OFFSET

def calculate_duration_minutes(start_time, end_time):
    try:
        sh, sm = map(int, start_time.split(':'))
        eh, em = map(int, end_time.split(':'))
        return (eh * 60 + em) - (sh * 60 + sm)
    except:
        return 60


def classify_task_type(title):
    """
    Scans the task title for keywords and returns a category weight.
    Higher weight = more academically important task.
    """
    title_lower = title.lower()

    academic_keywords = [
        'report', 'assignment', 'essay', 'exam', 'test', 'quiz',
        'paragraph', 'thesis', 'research', 'project', 'presentation',
        'submission', 'submit', 'dissertation', 'paper', 'homework',
        'lab', 'case study', 'viva', 'study', 'revision', 'midterm',
        'final exam', 'group project'
    ]

    moderate_keywords = [
        'meeting', 'class', 'lecture', 'reading', 'review',
        'practice', 'tutorial', 'workshop', 'seminar', 'discussion'
    ]

    routine_keywords = [
        'walk', 'dog', 'grocery', 'shopping', 'clean', 'laundry',
        'cook', 'gym', 'workout', 'sleep', 'relax', 'watch',
        'movie', 'game', 'hangout', 'call', 'chat', 'errand',
        'dishes', 'organize', 'tidy'
    ]

    for word in academic_keywords:
        if word in title_lower:
            return 25

    for word in moderate_keywords:
        if word in title_lower:
            return 12

    for word in routine_keywords:
        if word in title_lower:
            return 0

    return 8


def auto_assign_priority(title, due_date, start_time, end_time):
    """
    Automatically assigns High, Medium or Low priority
    based on the task's keyword type AND the deadline.
    No user input needed for any of it.
    """
    type_weight = classify_task_type(title)

    if not due_date:
        if type_weight >= 25:
            return 'Medium'
        return 'Low'

    hours_left = (due_date - now_npt()).total_seconds() / 3600
    duration = calculate_duration_minutes(start_time, end_time)

    urgency_points = 0
    if hours_left < 0:
        urgency_points = 50
    elif hours_left <= 24:
        urgency_points = 40
    elif hours_left <= 72:
        urgency_points = 25
    elif hours_left <= 168:
        urgency_points = 10
    else:
        urgency_points = 0

    duration_points = 10 if duration > 60 else 0

    total_points = type_weight + urgency_points + duration_points

    if total_points >= 45:
        return 'High'
    elif total_points >= 20:
        return 'Medium'
    else:
        return 'Low'


def score(task):
    # --- FACTOR 1: Auto assigned priority weight ---
    priority_weight = {'High': 30, 'Medium': 20, 'Low': 10}
    p = priority_weight.get(task.priority, 10)

    # --- FACTOR 1B: Task type weight (keyword detection) ---
    type_weight = classify_task_type(task.title)

    # --- FACTOR 2: Urgency based on exact hours left ---
    urgency = 0
    if task.due_date:
        hours_left = (task.due_date - now_npt()).total_seconds() / 3600
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

    # --- FACTOR 3: Duration bonus ---
    duration = calculate_duration_minutes(task.start_time, task.end_time)
    if duration <= 30:
        duration_bonus = 5
    elif duration <= 60:
        duration_bonus = 3
    else:
        duration_bonus = 0

    # --- FACTOR 4: Age bonus ---
    days_old = (now_npt() - task.created_at).days
    age_bonus = min(days_old, 10)

    return p + type_weight + urgency + duration_bonus + age_bonus


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
    today = now_npt().date()
    pending = [t for t in tasks if t.status != 'Done']
    return [t for t in pending if t.due_date and t.due_date.date() == today]


def get_overdue_tasks(tasks):
    now = now_npt()
    return [
        t for t in tasks
        if t.status != 'Done' and t.due_date and t.due_date < now
    ]


def get_next_task(tasks):
    prioritized = prioritize_tasks(tasks)
    return prioritized[0] if prioritized else None


def analyze_workload(tasks):
    from collections import defaultdict
    day_load = defaultdict(int)
    for task in tasks:
        if task.status == 'Done':
            continue
        if task.due_date:
            date_str = task.due_date.strftime('%Y-%m-%d')
            duration = calculate_duration_minutes(task.start_time, task.end_time)
            day_load[date_str] += duration

    result = {}
    for date_str, total_mins in day_load.items():
        if total_mins > 480:
            status = 'danger'
        elif total_mins > 300:
            status = 'warning'
        else:
            status = 'ok'
        result[date_str] = {
            'total_minutes': total_mins,
            'total_hours': round(total_mins / 60, 1),
            'status': status
        }
    return result


def get_productivity_stats(tasks):
    done = [t for t in tasks if t.status == 'Done']
    total = len(tasks)
    completed = len(done)
    completion_rate = round(
        (completed / total * 100) if total > 0 else 0, 1
    )

    completion_times = []
    for t in done:
        if t.completed_at and t.created_at:
            days = (t.completed_at - t.created_at).days
            completion_times.append(days)

    avg_completion_days = round(
        sum(completion_times) / len(completion_times), 1
    ) if len(completion_times) > 0 else 0

    priority_done = {'High': 0, 'Medium': 0, 'Low': 0}
    priority_total = {'High': 0, 'Medium': 0, 'Low': 0}
    for t in tasks:
        p = t.priority if t.priority in priority_total else 'Low'
        priority_total[p] = priority_total.get(p, 0) + 1
        if t.status == 'Done':
            priority_done[p] = priority_done.get(p, 0) + 1

    on_time = 0
    late = 0
    for t in done:
        if t.due_date and t.completed_at:
            if t.completed_at <= t.due_date:
                on_time += 1
            else:
                late += 1

    on_time_rate = round(
        (on_time / (on_time + late) * 100) if (on_time + late) > 0 else 0, 1
    )

    return {
        'completion_rate': completion_rate,
        'avg_completion_days': avg_completion_days,
        'priority_done': priority_done,
        'priority_total': priority_total,
        'on_time_rate': on_time_rate,
        'total': total,
        'completed': completed,
    }