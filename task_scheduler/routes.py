from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, Task, Notification
from scheduler import (
    prioritize_tasks, get_todays_tasks, get_overdue_tasks,
    get_next_task, analyze_workload, get_productivity_stats
)

main = Blueprint('main', _name_)
auth = Blueprint('auth', _name_)

# ───────────── AUTH ─────────────

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
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
        now=datetime.utcnow()
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

# ───────────── TASK API ─────────────

@main.route('/task/add', methods=['POST'])
@login_required
def add_task():
    data = request.get_json()
    due = datetime.strptime(data['due_date'], '%Y-%m-%d') if data.get('due_date') else None
    task = Task(
        title=data['title'],
        priority=data.get('priority', 'Medium'),
        status=data.get('status', 'Pending'),
        due_date=due,
        start_time=data.get('start_time', ''),
        end_time=data.get('end_time', ''),
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
    task.completed_at = datetime.utcnow()
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
    now = datetime.utcnow()
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