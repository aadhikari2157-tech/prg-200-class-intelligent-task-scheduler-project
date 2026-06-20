function openAddModal() {
  document.getElementById('add-modal').style.display = 'flex';
}

function closeModal() {
  document.getElementById('add-modal').style.display = 'none';
  document.getElementById('task-title').value = '';
  document.getElementById('task-due').value = '';
  document.getElementById('task-deadline-time').value = '';
  document.getElementById('task-start').value = '';
  document.getElementById('task-end').value = '';
  isSubmitting = false;

  const warningEl = document.getElementById('duplicate-warning');
  if (warningEl) warningEl.remove();
}

let isSubmitting = false;

async function submitTask() {
  if (isSubmitting) return;

  const title = document.getElementById('task-title').value.trim();
  if (!title) {
    alert('Please enter a task title.');
    return;
  }

  const due = document.getElementById('task-due').value;
  if (!due) {
    alert('Please enter a due date.');
    return;
  }

  isSubmitting = true;
  const btn = document.querySelector('.modal .btn-primary.full-width');
  if (btn) {
    btn.textContent = 'Adding...';
    btn.disabled = true;
  }

  const data = {
    title,
    due_date: due,
    deadline_time: document.getElementById('task-deadline-time').value,
    start_time: document.getElementById('task-start').value,
    end_time: document.getElementById('task-end').value,
  };

  const safetyTimeout = setTimeout(() => {
    isSubmitting = false;
    if (btn) {
      btn.textContent = 'Add Task';
      btn.disabled = false;
    }
    alert('Request took too long. Please check your connection and try again.');
  }, 8000);

  try {
    const res = await fetch('/task/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    clearTimeout(safetyTimeout);

    if (!res.ok && res.status !== 400) {
      throw new Error('Server error: ' + res.status);
    }

    const result = await res.json();

    if (result.success) {
      closeModal();
      location.reload();
    } else if (result.error === 'duplicate') {
      showDuplicateWarning(result.message);
    } else {
      alert(result.message || 'Could not add task. Please try again.');
    }
  } catch (err) {
    clearTimeout(safetyTimeout);
    console.error('Error adding task:', err);
    alert('Something went wrong while adding the task. Check the console for details.');
  } finally {
    isSubmitting = false;
    if (btn) {
      btn.textContent = 'Add Task';
      btn.disabled = false;
    }
  }
}

function showDuplicateWarning(message) {
  let warningEl = document.getElementById('duplicate-warning');
  if (!warningEl) {
    warningEl = document.createElement('div');
    warningEl.id = 'duplicate-warning';
    warningEl.className = 'duplicate-warning';
    const modalBody = document.querySelector('.modal-body');
    modalBody.insertBefore(warningEl, modalBody.firstChild);
  }
  warningEl.textContent = '⚠️ ' + message;
  warningEl.style.display = 'block';
}

document.addEventListener('click', (e) => {
  const modal = document.getElementById('add-modal');
  if (modal && e.target === modal) closeModal();
});

async function markDone(taskId, btn) {
  const res = await fetch(`/task/complete/${taskId}`, { method: 'POST' });
  const data = await res.json();
  if (data.success) {
    const el = document.getElementById(`task-${taskId}`);
    if (el) {
      el.style.opacity = '0.4';
      el.style.transition = 'opacity 0.4s';
    }
    setTimeout(() => location.reload(), 500);
  }
}

async function deleteTask(taskId) {
  if (!confirm('Delete this task?')) return;
  const res = await fetch(`/task/delete/${taskId}`, { method: 'POST' });
  const data = await res.json();
  if (data.success) {
    const el = document.getElementById(`task-${taskId}`);
    if (el) {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.3s';
      setTimeout(() => el.remove(), 300);
    }
  }
}

let notifOpen = false;

async function loadNotifications() {
  try {
    const res = await fetch('/notifications');
    const notifications = await res.json();
    const badge = document.getElementById('notif-badge');
    const list = document.getElementById('notif-list');
    if (!badge || !list) return;
    if (notifications.length > 0) {
      badge.textContent = notifications.length;
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }
    if (notifications.length === 0) {
      list.innerHTML = '<div class="notif-empty">You are all caught up! 🎉</div>';
      return;
    }
    list.innerHTML = notifications.map(n => `
      <div class="notif-item" id="notif-${n.id}">
        <div class="notif-message">${n.message}</div>
        <div class="notif-time">${n.created_at}</div>
        <button class="notif-dismiss" onclick="dismissNotif(${n.id})">✕</button>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load notifications:', err);
  }
}

function toggleNotifPanel() {
  const panel = document.getElementById('notif-panel');
  if (!panel) return;
  notifOpen = !notifOpen;
  if (notifOpen) {
    panel.style.display = 'block';
    loadNotifications();
  } else {
    panel.style.display = 'none';
  }
}

async function markAllRead() {
  await fetch('/notifications/read', { method: 'POST' });
  const badge = document.getElementById('notif-badge');
  const list = document.getElementById('notif-list');
  if (badge) badge.style.display = 'none';
  if (list) list.innerHTML = '<div class="notif-empty">You are all caught up! 🎉</div>';
  notifOpen = false;
  document.getElementById('notif-panel').style.display = 'none';
}

async function dismissNotif(notifId) {
  await fetch(`/notifications/read/${notifId}`, { method: 'POST' });
  const el = document.getElementById(`notif-${notifId}`);
  if (el) {
    el.style.opacity = '0';
    el.style.transition = 'opacity 0.3s';
    setTimeout(() => {
      el.remove();
      const remaining = document.querySelectorAll('.notif-item').length;
      const badge = document.getElementById('notif-badge');
      if (badge) {
        if (remaining === 0) {
          badge.style.display = 'none';
          document.getElementById('notif-list').innerHTML =
            '<div class="notif-empty">You are all caught up! 🎉</div>';
        } else {
          badge.textContent = remaining;
        }
      }
    }, 300);
  }
}

document.addEventListener('click', (e) => {
  const panel = document.getElementById('notif-panel');
  const btn = document.getElementById('notif-btn');
  if (panel && btn && !panel.contains(e.target) && !btn.contains(e.target)) {
    panel.style.display = 'none';
    notifOpen = false;
  }
});

window.addEventListener('load', () => {
  loadNotifications();
  setInterval(loadNotifications, 60000);
});