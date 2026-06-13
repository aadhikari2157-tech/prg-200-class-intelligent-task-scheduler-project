/* ═══════════════════════════════════════════════════════
   FlowTask AI — Frontend JavaScript v2
   Handles: task CRUD, NLP modal, notifications,
            auto-suggest priority/category, sidebar toggle
═══════════════════════════════════════════════════════ */

// ─────────────────────────────────────────────────────
// MODAL: Classic Add Task
// ─────────────────────────────────────────────────────

function openAddModal() {
  document.getElementById('add-modal').style.display = 'flex';
  setTimeout(() => document.getElementById('task-title').focus(), 50);
}

function closeAddModal(e) {
  if (!e || e.target === document.getElementById('add-modal')) {
    document.getElementById('add-modal').style.display = 'none';
  }
}

async function submitTask() {
  const title = document.getElementById('task-title').value.trim();
  if (!title) {
    showToast('Please enter a task title.', 'warning');
    return;
  }

  const data = {
    title,
    priority:        document.getElementById('task-priority').value,
    category:        document.getElementById('task-category').value,
    status:          'Pending',
    due_date:        document.getElementById('task-due').value,
    start_time:      document.getElementById('task-start').value,
    end_time:        document.getElementById('task-end').value,
    estimated_hours: parseFloat(document.getElementById('task-hours').value) || 1.0,
  };

  try {
    const res  = await fetch('/task/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const json = await res.json();
    if (json.success) {
      closeAddModal();
      showToast('Task added!', 'success');
      setTimeout(() => location.reload(), 600);
    } else {
      showToast(json.error || 'Failed to add task.', 'danger');
    }
  } catch (err) {
    showToast('Network error. Please try again.', 'danger');
  }
}

// ─────────────────────────────────────────────────────
// AUTO-SUGGEST PRIORITY
// ─────────────────────────────────────────────────────

async function autoSuggestPriority() {
  const dueDate = document.getElementById('task-due').value;
  const hours   = parseFloat(document.getElementById('task-hours').value) || 1.0;
  const chip    = document.getElementById('priority-suggestion');
  if (!dueDate) { chip.style.display = 'none'; return; }

  try {
    const res  = await fetch('/api/suggest-priority', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ due_date: dueDate, estimated_hours: hours }),
    });
    const json = await res.json();
    chip.style.display = 'flex';
    chip.innerHTML = `<i class="bi bi-stars me-1"></i><strong>AI suggests:</strong>&nbsp;${json.priority} — ${json.reason}`;
    // Auto-set select
    document.getElementById('task-priority').value = json.priority;
  } catch (_) { chip.style.display = 'none'; }
}

// ─────────────────────────────────────────────────────
// AUTO-SUGGEST CATEGORY
// ─────────────────────────────────────────────────────

let categoryDebounce;
async function autoSuggestCategory() {
  clearTimeout(categoryDebounce);
  categoryDebounce = setTimeout(async () => {
    const title = document.getElementById('task-title').value.trim();
    if (title.length < 3) return;
    try {
      const res  = await fetch('/api/suggest-category', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
      const json = await res.json();
      if (json.category) {
        document.getElementById('task-category').value = json.category;
      }
    } catch (_) {}
  }, 400);
}

// ─────────────────────────────────────────────────────
// MODAL: NLP Smart Add
// ─────────────────────────────────────────────────────

let nlpParsed = null;

function openNLPModal() {
  document.getElementById('nlp-modal').style.display = 'flex';
  document.getElementById('nlp-preview').style.display = 'none';
  document.getElementById('nlp-input').value = '';
  nlpParsed = null;
  setTimeout(() => document.getElementById('nlp-input').focus(), 50);
}

function closeNLPModal(e) {
  if (!e || e.target === document.getElementById('nlp-modal')) {
    document.getElementById('nlp-modal').style.display = 'none';
  }
}

function fillNLPExample(el) {
  document.getElementById('nlp-input').value = el.textContent;
}

async function parseNLP() {
  const text = document.getElementById('nlp-input').value.trim();
  if (!text) { showToast('Please enter a task description.', 'warning'); return; }

  try {
    const res  = await fetch('/api/nlp-parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    nlpParsed = await res.json();

    // Populate preview
    document.getElementById('np-title').textContent    = nlpParsed.title           || '—';
    document.getElementById('np-due').textContent      = nlpParsed.due_date
      ? nlpParsed.due_date + (nlpParsed.due_time ? ' at ' + nlpParsed.due_time : '')
      : 'Not detected';
    document.getElementById('np-priority').textContent = nlpParsed.priority        || 'Medium';
    document.getElementById('np-category').textContent = nlpParsed.category        || 'Other';
    document.getElementById('np-hours').textContent    = (nlpParsed.estimated_hours || 1) + 'h';

    document.getElementById('nlp-preview').style.display = 'block';
  } catch (err) {
    showToast('Parsing failed. Try again.', 'danger');
  }
}

async function submitNLPTask() {
  if (!nlpParsed) return;

  const data = {
    title:           nlpParsed.title,
    priority:        nlpParsed.priority        || 'Medium',
    category:        nlpParsed.category        || 'Other',
    due_date:        nlpParsed.due_date        || '',
    estimated_hours: nlpParsed.estimated_hours || 1.0,
    nlp_raw:         document.getElementById('nlp-input').value.trim(),
    status:          'Pending',
  };

  try {
    const res  = await fetch('/task/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const json = await res.json();
    if (json.success) {
      closeNLPModal();
      showToast(`"${data.title}" added as ${json.category || data.category}!`, 'success');
      setTimeout(() => location.reload(), 700);
    } else {
      showToast(json.error || 'Failed to add task.', 'danger');
    }
  } catch (_) {
    showToast('Network error.', 'danger');
  }
}

// ─────────────────────────────────────────────────────
// TASK ACTIONS
// ─────────────────────────────────────────────────────

async function markDone(taskId, el) {
  try {
    const res  = await fetch(`/task/complete/${taskId}`, { method: 'POST' });
    const json = await res.json();
    if (json.success) {
      // Animate the row out
      const row = document.getElementById(`task-${taskId}`);
      if (row) {
        row.style.transition = 'opacity .35s, transform .35s';
        row.style.opacity = '0';
        row.style.transform = 'translateX(16px)';
        setTimeout(() => row.remove(), 360);
      }
      showToast('Task marked as done! ✅', 'success');
      // Refresh after short delay to update KPIs
      setTimeout(() => location.reload(), 1200);
    }
  } catch (_) {
    showToast('Failed to complete task.', 'danger');
  }
}

async function deleteTask(taskId) {
  if (!confirm('Delete this task?')) return;
  try {
    const res  = await fetch(`/task/delete/${taskId}`, { method: 'POST' });
    const json = await res.json();
    if (json.success) {
      const row = document.getElementById(`task-${taskId}`);
      if (row) {
        row.style.transition = 'opacity .25s, transform .25s';
        row.style.opacity = '0';
        row.style.transform = 'scale(.97)';
        setTimeout(() => row.remove(), 260);
      }
      showToast('Task deleted.', 'info');
    }
  } catch (_) {
    showToast('Failed to delete task.', 'danger');
  }
}

// ─────────────────────────────────────────────────────
// NOTIFICATIONS
// ─────────────────────────────────────────────────────

let notifOpen = false;

async function loadNotifications() {
  try {
    const res   = await fetch('/notifications');
    const items = await res.json();

    const badge = document.getElementById('notif-badge');
    const list  = document.getElementById('notif-list');
    if (!badge || !list) return;

    if (items.length > 0) {
      badge.style.display = 'block';
    } else {
      badge.style.display = 'none';
    }

    if (!items.length) {
      list.innerHTML = '<div class="notif-empty"><i class="bi bi-check-circle me-1"></i>All caught up!</div>';
      return;
    }

    list.innerHTML = items.map(n => `
      <div class="notif-item notif-item-${n.type}" id="notif-${n.id}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <span>${n.message}</span>
          <button class="notif-dismiss" onclick="dismissNotif(${n.id})">✕</button>
        </div>
        <div class="notif-time">${n.created_at}</div>
      </div>`).join('');
  } catch (_) {}
}

function toggleNotifPanel() {
  const panel = document.getElementById('notif-panel');
  if (!panel) return;
  notifOpen = !notifOpen;
  panel.style.display = notifOpen ? 'block' : 'none';
  if (notifOpen) loadNotifications();
}

async function markAllRead() {
  await fetch('/notifications/read', { method: 'POST' });
  const badge = document.getElementById('notif-badge');
  if (badge) badge.style.display = 'none';
  const list = document.getElementById('notif-list');
  if (list) list.innerHTML = '<div class="notif-empty"><i class="bi bi-check-circle me-1"></i>All caught up!</div>';
  notifOpen = false;
  document.getElementById('notif-panel').style.display = 'none';
}

async function dismissNotif(id) {
  await fetch(`/notifications/read/${id}`, { method: 'POST' });
  const el = document.getElementById(`notif-${id}`);
  if (el) {
    el.style.opacity = '0';
    setTimeout(() => {
      el.remove();
      // Update badge
      const remaining = document.querySelectorAll('.notif-item').length;
      if (remaining === 0) {
        document.getElementById('notif-badge').style.display = 'none';
        document.getElementById('notif-list').innerHTML =
          '<div class="notif-empty"><i class="bi bi-check-circle me-1"></i>All caught up!</div>';
      }
    }, 200);
  }
}

// Close notif panel when clicking outside
document.addEventListener('click', (e) => {
  const panel = document.getElementById('notif-panel');
  const btn   = document.getElementById('notif-btn');
  if (notifOpen && panel && btn
      && !panel.contains(e.target)
      && !btn.contains(e.target)) {
    panel.style.display = 'none';
    notifOpen = false;
  }
});

// ─────────────────────────────────────────────────────
// SIDEBAR TOGGLE (mobile)
// ─────────────────────────────────────────────────────

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ─────────────────────────────────────────────────────
// TOAST NOTIFICATIONS
// ─────────────────────────────────────────────────────

function showToast(message, type = 'info') {
  // Remove existing toasts
  document.querySelectorAll('.flowtask-toast').forEach(t => t.remove());

  const colors = {
    success: '#22c55e',
    danger:  '#ef4444',
    warning: '#f59e0b',
    info:    '#6366f1',
  };

  const toast = document.createElement('div');
  toast.className = 'flowtask-toast';
  toast.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 9999;
    background: #1e293b; color: #fff;
    padding: 12px 18px; border-radius: 10px;
    font-size: 13.5px; font-weight: 500;
    display: flex; align-items: center; gap: 10px;
    box-shadow: 0 8px 24px rgba(0,0,0,.2);
    animation: toast-in .25s ease;
    border-left: 4px solid ${colors[type] || colors.info};
    font-family: 'Sora', sans-serif;
    max-width: 340px;
  `;

  const icons = { success: 'check-circle-fill', danger: 'exclamation-triangle-fill',
                  warning: 'exclamation-circle-fill', info: 'info-circle-fill' };
  toast.innerHTML = `<i class="bi bi-${icons[type] || icons.info}" style="color:${colors[type]};font-size:16px"></i>${message}`;

  // Add animation keyframe once
  if (!document.getElementById('toast-style')) {
    const s = document.createElement('style');
    s.id = 'toast-style';
    s.textContent = '@keyframes toast-in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}';
    document.head.appendChild(s);
  }

  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'opacity .25s, transform .25s';
    setTimeout(() => toast.remove(), 260);
  }, 3200);
}

// ─────────────────────────────────────────────────────
// KEYBOARD SHORTCUTS
// ─────────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
  // Cmd/Ctrl + K → NLP modal
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    openNLPModal();
  }
  // Cmd/Ctrl + N → regular add modal
  if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
    e.preventDefault();
    openAddModal();
  }
  // Escape → close any open modal
  if (e.key === 'Escape') {
    document.getElementById('add-modal').style.display = 'none';
    document.getElementById('nlp-modal').style.display = 'none';
    const panel = document.getElementById('notif-panel');
    if (panel) panel.style.display = 'none';
    notifOpen = false;
  }
  // Enter in NLP input → parse
  if (e.key === 'Enter' && document.activeElement?.id === 'nlp-input') {
    parseNLP();
  }
});

// ─────────────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────────────

window.addEventListener('load', () => {
  // Load notification badge count silently (no panel)
  loadNotificationCount();
  // Refresh count every 60 seconds
  setInterval(loadNotificationCount, 60000);
});

async function loadNotificationCount() {
  try {
    const res   = await fetch('/notifications');
    const items = await res.json();
    const badge = document.getElementById('notif-badge');
    if (badge) badge.style.display = items.length > 0 ? 'block' : 'none';
  } catch (_) {}
}
