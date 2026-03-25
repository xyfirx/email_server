const API = '/mail/';
let currentUser = null;
let currentFolder = 'inbox';
let currentEmailId = null;
let currentDraftId = null;
let composeMaximized = false;

const FOLDER_LABELS = {
  inbox: 'Входящие',
  sent: 'Отправленные',
  draft: 'Черновики',
  archive: 'Архив',
  trash: 'Корзина',
};

function apiJson(path, method = 'GET', body = null) {
  const options = {
    method,
    credentials: 'same-origin',
    headers: {'Content-Type': 'application/json'},
  };
  if (body) options.body = JSON.stringify(body);

  return fetch(API + path, options).then(async (response) => {
    let payload = {};
    try {
      payload = await response.json();
    } catch (_) {}

    if (!response.ok) {
      const error = new Error(payload.message || `HTTP ${response.status}`);
      error.status = response.status;
      throw error;
    }
    return payload;
  });
}

function apiForm(path, formData) {
  return fetch(API + path, {
    method: 'POST',
    credentials: 'same-origin',
    body: formData,
  }).then(async (response) => {
    let payload = {};
    try {
      payload = await response.json();
    } catch (_) {}

    if (!response.ok) {
      const error = new Error(payload.message || `HTTP ${response.status}`);
      error.status = response.status;
      throw error;
    }
    return payload;
  });
}

function openModal(id) {
  document.getElementById(id).classList.add('open');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

function switchModal(from, to) {
  closeModal(from);
  openModal(to);
}

function esc(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderHeader() {
  const area = document.getElementById('header-user');

  if (currentUser) {
    const letter = currentUser.username.charAt(0).toUpperCase();
    area.innerHTML = `
      <div class="user-badge">
        <div class="user-avatar">${letter}</div>
        <span class="user-email-txt">${esc(currentUser.email)}</span>
        <button class="btn-logout" id="btn-logout">Выйти</button>
      </div>
    `;
    document.getElementById('btn-logout').addEventListener('click', doLogout);
  } else {
    area.innerHTML = `
      <button class="btn-auth" id="open-login">Войти</button>
      <button class="btn-auth primary" id="open-register">Регистрация</button>
    `;
    document.getElementById('open-login').addEventListener('click', () => {
      openModal('modal-login');
    });
    document.getElementById('open-register').addEventListener('click', () => {
      openModal('modal-reg');
    });
  }
}

function renderNotLoggedIn() {
  document.getElementById('email-list').innerHTML = `
    <div class="auth-prompt">
      <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5">
        <rect x="2" y="4" width="20" height="16" rx="2"/>
        <path d="M2 7l10 7 10-7"/>
      </svg>
      <div>Войдите, чтобы читать почту</div>
    </div>
  `;
  closeEmailView();
}

function refreshBadges(folder, emails) {
  if (folder === 'inbox') {
    const unread = emails.filter((email) => !email.is_read).length;
    const badge = document.getElementById('badge-inbox');
    badge.textContent = unread || '';
    badge.classList.toggle('show', unread > 0);
  }

  if (folder === 'draft') {
    const badge = document.getElementById('badge-draft');
    badge.textContent = emails.length || '';
    badge.classList.toggle('show', emails.length > 0);
  }
}

function renderEmailList(emails, folder) {
  const list = document.getElementById('email-list');
  if (!emails.length) {
    const label = FOLDER_LABELS[folder] || folder;
    list.innerHTML = `
      <div class="empty-folder">
        <div style="font-size:2.5rem;opacity:.3">&#9993;</div>
        <div>${label} пусты</div>
      </div>
    `;
    return;
  }

  list.innerHTML = emails.map((email) => {
    const unreadClass = !email.is_read && folder === 'inbox' ? ' unread' : '';
    const attach = email.has_attachment ? ' &#128206;' : '';
    const sender = (folder === 'sent' || folder === 'draft')
      ? (email.receiver_email || 'Черновик')
      : email.sender_email;
    const preview = email.body_preview
      ? ` &mdash; <span class="email-preview">${esc(email.body_preview)}</span>`
      : '';
    const readMark = folder === 'inbox'
      ? `<span class="email-read-mark">${email.is_read ? 'Прочитано' : 'Новое'}</span>`
      : '';

    const trashButton = (folder !== 'trash' && folder !== 'sent')
      ? `<button class="row-trash-btn" data-trash-id="${email.id}" title="В корзину">&#128465;</button>`
      : '';

    return `
      <div class="email-row${unreadClass}" data-email-id="${email.id}">
        <div class="email-from">${esc(sender)}</div>
        ${readMark}
        <div class="email-subject">${esc(email.subject)}${preview}${attach}</div>
        <div class="email-actions">${trashButton}</div>
        <div class="email-date">${email.date}</div>
      </div>
    `;
  }).join('');

  list.querySelectorAll('.email-row').forEach((row) => {
    row.addEventListener('click', () => {
      const emailId = Number(row.dataset.emailId);
      openEmail(emailId);
    });
  });

  list.querySelectorAll('.row-trash-btn').forEach((button) => {
    button.addEventListener('click', (event) => {
      event.stopPropagation();
      const emailId = Number(button.dataset.trashId);
      moveEmailToTrash(emailId);
    });
  });
}

function loadFolder(folder, keepOpenedView = false) {
  currentFolder = folder;
  if (!keepOpenedView) {
    currentEmailId = null;
    closeEmailView();
  }

  document.querySelectorAll('.nav-item').forEach((item) => {
    item.classList.toggle('active', item.dataset.folder === folder);
  });
  document.getElementById('folder-title').textContent = FOLDER_LABELS[folder] || folder;
  if (!currentUser) {
    renderNotLoggedIn();
    return;
  }

  const list = document.getElementById('email-list');
  list.innerHTML = '<div style="padding:24px;color:#aaa;font-size:.9rem">Загрузка...</div>';

  apiJson(`emails/${folder}/`)
    .then((emails) => {
      renderEmailList(emails, folder);
      refreshBadges(folder, emails);
    })
    .catch((error) => {
      list.innerHTML = `<div class="empty-folder"><p>${esc(error.message)}</p></div>`;
    });
}

function renderEmailView(email) {
  document.getElementById('ev-subject').textContent = email.subject;
  document.getElementById('ev-meta').innerHTML = `
    <strong>От:</strong> ${esc(email.sender_email)}<br>
    <strong>Кому:</strong> ${esc(email.receiver_email || '—')}<br>
    <strong>Статус:</strong> ${esc(email.read_status || 'Неизвестно')}<br>
    <strong>Дата:</strong> ${email.date}
  `;

  let bodyHtml = esc(email.body || '');
  if (email.attachment_url) {
    bodyHtml += `<br><br>&#128206; <a href="${email.attachment_url}" target="_blank" rel="noopener">${esc(email.attachment_name)}</a>`;
  }
  document.getElementById('ev-body').innerHTML = bodyHtml;

  const actions = document.getElementById('ev-actions');
  actions.innerHTML = '';

  if (email.folder === 'draft') {
    const editButton = document.createElement('button');
    editButton.className = 'action-btn';
    editButton.innerHTML = '&#9998; Редактировать';
    editButton.addEventListener('click', () => editDraft(email.id));
    actions.appendChild(editButton);
  }

  if (email.folder !== 'trash' && email.folder !== 'sent') {
    const moveTrashButton = document.createElement('button');
    moveTrashButton.className = 'action-btn';
    moveTrashButton.innerHTML = '&#128465; В корзину';
    moveTrashButton.addEventListener('click', () => moveEmail('trash'));
    actions.appendChild(moveTrashButton);

    if (email.folder !== 'archive') {
      const moveArchiveButton = document.createElement('button');
      moveArchiveButton.className = 'action-btn';
      moveArchiveButton.innerHTML = '&#128230; В архив';
      moveArchiveButton.addEventListener('click', () => moveEmail('archive'));
      actions.appendChild(moveArchiveButton);
    }
  }

  if (email.folder === 'trash') {
    const restoreButton = document.createElement('button');
    restoreButton.className = 'action-btn';
    restoreButton.innerHTML = '&#8617; Восстановить';
    restoreButton.addEventListener('click', () => restoreEmailFromTrash(email));
    actions.appendChild(restoreButton);

    const deleteButton = document.createElement('button');
    deleteButton.className = 'action-btn danger';
    deleteButton.innerHTML = '&#128465; Удалить навсегда';
    deleteButton.addEventListener('click', deleteEmailForever);
    actions.appendChild(deleteButton);
  }

  if (email.folder === 'archive') {
    const restoreArchiveButton = document.createElement('button');
    restoreArchiveButton.className = 'action-btn';
    restoreArchiveButton.innerHTML = '&#8617; Из архива во входящие';
    restoreArchiveButton.addEventListener('click', () => moveEmail('inbox'));
    actions.appendChild(restoreArchiveButton);
  }

  document.getElementById('email-view').classList.add('open');
}

function openEmail(id) {
  currentEmailId = id;
  apiJson(`email/${id}/`)
    .then((email) => {
      renderEmailView(email);
      loadFolder(currentFolder, true);
    })
    .catch((error) => alert(error.message));
}

function moveEmailToTrash(emailId) {
  apiJson(`email/${emailId}/move/`, 'PUT', {folder: 'trash'})
    .then(() => {
      if (currentEmailId === emailId) {
        closeEmailView();
      }
      loadFolder(currentFolder);
    })
    .catch((error) => alert(error.message));
}

function restoreEmailFromTrash(email) {
  if (!email || email.folder !== 'trash') return;
  const targetFolder = email.sender_email === currentUser.email
    ? 'sent'
    : 'inbox';
  moveEmail(targetFolder);
}

function closeEmailView() {
  document.getElementById('email-view').classList.remove('open');
  currentEmailId = null;
}

function moveEmail(folder) {
  if (!currentEmailId) return;
  apiJson(`email/${currentEmailId}/move/`, 'PUT', {folder})
    .then(() => {
      closeEmailView();
      loadFolder(currentFolder);
    })
    .catch((error) => alert(error.message));
}

function deleteEmailForever() {
  if (!currentEmailId) return;
  if (!confirm('Удалить письмо безвозвратно?')) return;

  fetch(`${API}email/${currentEmailId}/delete/`, {
    method: 'DELETE',
    credentials: 'same-origin',
  }).then(() => {
    closeEmailView();
    loadFolder(currentFolder);
  });
}

function openComposePanel(prefill = {}) {
  if (!currentUser) {
    openModal('modal-login');
    return;
  }

  document.getElementById('c-to').value = prefill.to || '';
  document.getElementById('c-subject').value = prefill.subject || '';
  document.getElementById('c-body').value = prefill.body || '';
  document.getElementById('c-file-name').textContent = '';
  document.getElementById('c-msg').textContent = '';
  document.getElementById('c-file').value = '';
  currentDraftId = prefill.draftId || null;
  const panel = document.getElementById('compose-panel');
  panel.classList.remove('minimized');
  panel.classList.add('open');
}

function toggleComposeMinimize() {
  const panel = document.getElementById('compose-panel');
  panel.classList.toggle('minimized');
}

function toggleComposeMaximize() {
  const panel = document.getElementById('compose-panel');
  composeMaximized = !composeMaximized;
  panel.classList.toggle('maximized', composeMaximized);
  panel.classList.remove('minimized');
}

function editDraft(id) {
  apiJson(`email/${id}/`).then((email) => {
    openComposePanel({
      to: email.receiver_email,
      subject: email.subject,
      body: email.body,
      draftId: id,
    });
  });
}

function submitCompose(isDraft) {
  const to = document.getElementById('c-to').value.trim();
  const subject = document.getElementById('c-subject').value.trim();
  const body = document.getElementById('c-body').value.trim();
  const file = document.getElementById('c-file').files[0];
  const message = document.getElementById('c-msg');

  if (!isDraft && !to) {
    message.style.color = '#EA4335';
    message.textContent = 'Укажите адрес получателя';
    return;
  }

  const formData = new FormData();
  formData.append('to_email', to);
  formData.append('subject', subject);
  formData.append('body', body);
  formData.append('draft', isDraft ? '1' : '0');
  if (file) formData.append('attachment', file);

  const doSend = () => apiForm('send/', formData)
    .then((response) => {
      message.style.color = '#34A853';
      message.textContent = response.message;
      setTimeout(() => {
        document.getElementById('compose-panel').classList.remove('open');
        loadFolder(currentFolder);
      }, 1000);
    })
    .catch((error) => {
      message.style.color = '#EA4335';
      message.textContent = error.message;
    });

  if (currentDraftId) {
    fetch(`${API}email/${currentDraftId}/delete/`, {
      method: 'DELETE',
      credentials: 'same-origin',
    }).finally(doSend);
  } else {
    doSend();
  }
}

function doRegister() {
  const username = document.getElementById('r-user').value.trim();
  const password = document.getElementById('r-pass').value;
  const error = document.getElementById('r-err');
  error.textContent = '';

  if (!username || !password) {
    error.textContent = 'Заполните все поля';
    return;
  }

  apiJson('register/', 'POST', {username, password})
    .then((user) => {
      currentUser = user;
      closeModal('modal-reg');
      renderHeader();
      loadFolder('inbox');
    })
    .catch((err) => {
      error.textContent = err.message;
    });
}

function doLogin() {
  const username = document.getElementById('l-user').value.trim();
  const password = document.getElementById('l-pass').value;
  const error = document.getElementById('l-err');
  error.textContent = '';

  if (!username || !password) {
    error.textContent = 'Заполните все поля';
    return;
  }

  apiJson('login/', 'POST', {username, password})
    .then((user) => {
      currentUser = user;
      closeModal('modal-login');
      renderHeader();
      loadFolder('inbox');
    })
    .catch((err) => {
      error.textContent = err.message;
    });
}

function doLogout() {
  apiJson('logout/', 'POST').finally(() => {
    currentUser = null;
    renderHeader();
    closeEmailView();
    renderNotLoggedIn();
  });
}

function initApp() {
  document.querySelectorAll('.modal-bg').forEach((bg) => {
    bg.addEventListener('click', (event) => {
      if (event.target === bg) bg.classList.remove('open');
    });
  });

  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', () => loadFolder(item.dataset.folder));
  });

  document.getElementById('btn-compose').addEventListener('click', () => {
    openComposePanel();
  });

  document.getElementById('compose-close').addEventListener('click', () => {
    document.getElementById('compose-panel').classList.remove('open');
  });

  document.getElementById('compose-minimize').addEventListener('click', () => {
    toggleComposeMinimize();
  });

  document.getElementById('compose-maximize').addEventListener('click', () => {
    toggleComposeMaximize();
  });

  document.getElementById('c-send').addEventListener('click', () => {
    submitCompose(false);
  });

  document.getElementById('c-draft').addEventListener('click', () => {
    submitCompose(true);
  });

  document.getElementById('c-file').addEventListener('change', function () {
    document.getElementById('c-file-name').textContent = this.files[0]
      ? this.files[0].name
      : '';
  });

  document.getElementById('ev-close').addEventListener('click', closeEmailView);
  document.getElementById('l-submit').addEventListener('click', doLogin);
  document.getElementById('r-submit').addEventListener('click', doRegister);

  document.getElementById('l-pass').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') doLogin();
  });

  document.getElementById('r-pass').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') doRegister();
  });

  document.getElementById('r-user').addEventListener('input', function () {
    document.getElementById('preview-addr').textContent =
      `${this.value.trim() || 'username'}@tmal.ru`;
  });

  apiJson('current_user/')
    .then((user) => {
      currentUser = user.id ? user : null;
      renderHeader();
      if (currentUser) {
        loadFolder('inbox');
      } else {
        renderNotLoggedIn();
      }
    })
    .catch(() => {
      currentUser = null;
      renderHeader();
      renderNotLoggedIn();
    });
}

initApp();
