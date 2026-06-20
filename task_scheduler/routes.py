from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from scheduler import now_npt
from models import db, User, Task, Notification
from scheduler import (
    prioritize_tasks, get_todays_tasks, get_overdue_tasks,
    get_next_task, analyze_workload, get_productivity_stats,
    auto_assign_priority
)

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
main = Blueprint('main',  __name__)
auth = Blueprint('auth', __name__)

# ───────────── AUTH ─────────────

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        raw_password = request.form['password']

        # Password strength validation
        import re
        errors = []
        if len(raw_password) < 8:
            errors.append('at least 8 characters')
        if not re.search(r'[0-9]', raw_password):
            errors.append('at least one number (0-9)')
        if not re.search(r'[@#$%^&*!]', raw_password):
            errors.append('at least one special character (@ # $ % ^ & * !)')
        if not re.search(r'[A-Z]', raw_password):
            errors.append('at least one uppercase letter')

        if errors:
            flash(
                'Weak password. Your password needs: ' + ', '.join(errors) + '.',
                'danger'
            )
            return render_template('register.html')

        password = generate_password_hash(raw_password)
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# ───────────── MAIN PAGES ─────────────

@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    total = len(tasks)
    completed = len([t for t in tasks if t.status == 'Done'])
    in_progress = len([t for t in tasks if t.status == 'In Progress'])
    overdue_tasks = get_overdue_tasks(tasks)
    overdue = len(overdue_tasks)
    today_tasks = get_todays_tasks(tasks)
    done_tasks = [t for t in tasks if t.status == 'Done']
    next_task = get_next_task(tasks)
    workload = analyze_workload(tasks)
    smart_order = prioritize_tasks(tasks)
    return render_template('dashboard.html',
        tasks=tasks,
        smart_order=smart_order,
        today_tasks=today_tasks,
        done_tasks=done_tasks,
        next_task=next_task,
        workload=workload,
        overdue_tasks=overdue_tasks,
        total=total,
        completed=completed,
        in_progress=in_progress,
        overdue=overdue,
        now=now_npt()
    )

@main.route('/calendar')
@login_required
def calendar():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    total = len(tasks)
    completed = len([t for t in tasks if t.status == 'Done'])
    in_progress = len([t for t in tasks if t.status == 'In Progress'])
    overdue = len(get_overdue_tasks(tasks))

    tasks_data = []
    for t in tasks:
        tasks_data.append({
            'id': t.id,
            'title': t.title,
            'priority': t.priority,
            'status': t.status,
            'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else '',
            'start_time': t.start_time if t.start_time else '',
            'end_time': t.end_time if t.end_time else ''
        })

    return render_template('calendar.html',
        tasks=tasks_data,
        total=total,
        completed=completed,
        in_progress=in_progress,
        overdue=overdue
    )

@main.route('/reports')
@login_required
def reports():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    stats = get_productivity_stats(tasks)
    workload = analyze_workload(tasks)
    return render_template('reports.html', tasks=tasks, stats=stats, workload=workload)

@main.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# ───────────── TASK API ─────────────
@main.route('/task/add', methods=['POST'])
@login_required
def add_task():
    data = request.get_json()

    title = data.get('title', '').strip()
    start = data.get('start_time', '').strip()
    end = data.get('end_time', '').strip()
    deadline_time = data.get('deadline_time', '').strip()
    due_date_str = data.get('due_date', '').strip()

    due = None
    if due_date_str:
        if deadline_time:
            due = datetime.strptime(f"{due_date_str} {deadline_time}", '%Y-%m-%d %H:%M')
        else:
            due = datetime.strptime(due_date_str, '%Y-%m-%d')

    # ───── DUPLICATE TASK CHECK ─────
    existing_tasks = Task.query.filter_by(user_id=current_user.id, status='Pending').all()

    new_due_str = due.strftime('%Y-%m-%d %H:%M') if due else ''

    print("=== DUPLICATE CHECK DEBUG ===")
    print(f"New task -> due: '{new_due_str}', start: '{start}', end: '{end}'")

    for t in existing_tasks:
        existing_due_str = t.due_date.strftime('%Y-%m-%d %H:%M') if t.due_date else ''
        existing_start = (t.start_time or '').strip()
        existing_end = (t.end_time or '').strip()

        print(f"Existing task '{t.title}' -> due: '{existing_due_str}', start: '{existing_start}', end: '{existing_end}'")

        if existing_due_str == new_due_str and existing_start == start and existing_end == end:
            print("DUPLICATE FOUND - BLOCKING")
            return jsonify({
                'success': False,
                'error': 'duplicate',
                'message': f'Duplicate task not accepted. "{t.title}" already has the same deadline and work time.'
            }), 400

    print("No duplicate found - proceeding to create task")

    auto_priority = auto_assign_priority(title, due, start, end)

    task = Task(
        title=title,
        priority=auto_priority,
        status='Pending',
        due_date=due,
        deadline_time=deadline_time,
        start_time=start,
        end_time=end,
        user_id=current_user.id
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({'success': True, 'id': task.id})

@main.route('/task/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.status = 'Done'
    task.completed_at = now_npt()
    db.session.commit()
    return jsonify({'success': True})

@main.route('/task/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})

@main.route('/tasks/json')
@login_required
def tasks_json():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    result = []
    for t in tasks:
        result.append({
            'id': t.id,
            'title': t.title,
            'priority': t.priority,
            'status': t.status,
            'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else '',
            'start_time': t.start_time,
            'end_time': t.end_time
        })
    return jsonify(result)

# ───────────── NOTIFICATIONS ─────────────

def generate_notifications(user_id, tasks):
    now = now_npt()
    for task in tasks:
        if task.status == 'Done':
            continue
        if not task.due_date:
            continue
        hours_left = (task.due_date - now).total_seconds() / 3600
        existing = Notification.query.filter_by(
            user_id=user_id,
            task_id=task.id,
            is_read=False
        ).first()
        if existing:
            continue
        if hours_left < 0:
            msg = f'⚠️ "{task.title}" is overdue!'
            notif = Notification(user_id=user_id, task_id=task.id, message=msg)
            db.session.add(notif)
        elif hours_left <= 24:
            msg = f'🔔 "{task.title}" is due in {int(hours_left)} hours.'
            notif = Notification(user_id=user_id, task_id=task.id, message=msg)
            db.session.add(notif)
        elif hours_left <= 48:
            msg = f'📅 "{task.title}" is due tomorrow.'
            notif = Notification(user_id=user_id, task_id=task.id, message=msg)
            db.session.add(notif)
    db.session.commit()


@main.route('/notifications')
@login_required
def get_notifications():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    generate_notifications(current_user.id, tasks)
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'created_at': n.created_at.strftime('%b %d, %H:%M'),
        'is_read': n.is_read
    } for n in notifications])


@main.route('/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})


@main.route('/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_one_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})