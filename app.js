const $ = (sel, root = document) => root.querySelector(sel);
function html(el, content) { if (typeof content === 'string') el.innerHTML = content; else el.appendChild(content); }
function navigate(path) { window.location.hash = path; }
function escapeHtml(text) { if (!text) return ''; const d = document.createElement('div'); d.textContent = text; return d.innerHTML; }

function showError(message) {
  const app = $('#app');
  app.innerHTML = `<div class="min-h-screen flex items-center justify-center bg-gray-100 px-4"><div class="w-full max-w-md space-y-6"><div class="bg-red-50 border border-red-200 p-6 rounded-xl text-center"><div class="w-12 h-12 rounded-full bg-red-200 flex items-center justify-center mx-auto mb-4"><i class="fa-solid fa-triangle-exclamation text-red-600 text-xl"></i></div><h3 class="text-lg font-semibold text-gray-900">Ошибка приложения</h3><p class="text-sm text-gray-700 mt-2">${escapeHtml(message)}</p><button onclick="location.reload()" class="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition">Обновить страницу</button></div></div></div>`;
}

const state = { user: null, campaigns: [], currentCampaignId: null, modFilter: 'all' };

const routes = {
  '#login': renderLogin,
  '#advertiser/dashboard': renderAdvDashboard,
  '#advertiser/create': renderAdvCreate,
  '#advertiser/topup': renderAdvTopup,
  '#moderator/dashboard': renderModDashboard,
  '#moderator/campaign': renderModCampaign,
};

function router() {
  try {
    const hash = window.location.hash || '#login';
    const app = $('#app');
    const viewName = hash.split('?')[0];
    if (!state.user && viewName !== '#login') { navigate('#login'); return; }
    if (state.user && viewName === '#login') {
      navigate(state.user.role === 'moderator' ? '#moderator/dashboard' : '#advertiser/dashboard');
      return;
    }
    const render = routes[viewName];
    if (render) render(app); else renderLogin(app);
  } catch (e) { showError(e.message); }
}

window.addEventListener('hashchange', router);
window.addEventListener('error', (e) => { showError('Ошибка скрипта: ' + (e.message || 'неизвестная ошибка')); });
window.addEventListener('unhandledrejection', (e) => { showError('Ошибка: ' + (e.reason && e.reason.message ? e.reason.message : String(e.reason))); });
async function loginAs(role) {
  try { const data = await api.login(role); localStorage.setItem('adplatform_token', data.token); state.user = data.user; router(); }
  catch (e) { alert('Ошибка входа: ' + e.message); }
}

async function logout() {
  try { await api.logout(); } catch (e) { console.error(e); }
  localStorage.removeItem('adplatform_token');
  state.user = null; state.currentCampaignId = null; navigate('#login');
}

function navbar() {
  const isMod = state.user.role === 'moderator';
  return `<nav class="sticky top-0 z-20 bg-white border-b border-gray-100"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div class="flex items-center justify-between h-16"><div class="flex items-center gap-2"><div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white text-sm font-bold">AP</div><span class="font-bold text-gray-900">AdPlatform</span></div><div class="hidden md:flex items-center gap-6">${isMod ? '<a href="#moderator/dashboard" class="text-sm font-medium text-gray-600 hover:text-blue-600 transition">Панель модератора</a>' : '<a href="#advertiser/dashboard" class="text-sm font-medium text-gray-600 hover:text-blue-600 transition">Мои кампании</a><a href="#advertiser/topup" class="text-sm font-medium text-gray-600 hover:text-blue-600 transition">Пополнить баланс</a>'}<button onclick="logout()" class="text-sm font-medium text-gray-600 hover:text-red-600 transition flex items-center gap-1"><i class="fa-solid fa-sign-out-alt"></i> Выход</button></div><div class="flex items-center gap-3"><span class="hidden sm:block text-sm font-medium text-gray-700">${state.user.name}</span><div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-semibold text-gray-600">${state.user.name.charAt(0)}</div></div></div></div></nav>`;
}

function renderLogin(root) {
  html(root, `<div class="min-h-screen flex items-center justify-center bg-gray-100 px-4"><div class="w-full max-w-md space-y-6"><div class="text-center"><div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 text-white mb-4 shadow-lg"><i class="fa-solid fa-billboard text-2xl"></i></div><h1 class="text-2xl font-bold text-gray-900">AdPlatform</h1><p class="text-gray-500 text-sm">Платформа управления рекламными кампаниями</p></div><div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 space-y-5"><h2 class="text-lg font-semibold text-gray-800">Вход в кабинет</h2><button onclick="loginAs('advertiser')" class="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-200 rounded-xl bg-white text-gray-700 font-medium hover:bg-gray-50 transition"><span class="flex items-center gap-2"><i class="fa-brands fa-google text-red-500"></i> Войти через OAuth</span></button><div class="relative"><div class="absolute inset-0 flex items-center"><span class="w-full border-t border-gray-200"></span></div><span class="relative text-xs font-medium text-gray-400 bg-white px-2">или продолжить как</span></div><button onclick="loginAs('moderator')" class="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 text-gray-700 font-medium hover:bg-gray-100 transition"><i class="fa-solid fa-user-shield text-indigo-600"></i> Войти как модератор</button></div></div></div></div>`);
}


window.addEventListener('load', async () => {
  const token = localStorage.getItem('adplatform_token');
  if (token) {
    try { state.user = await api.me(); router(); } catch (e) { localStorage.removeItem('adplatform_token'); navigate('#login'); }
  } else { router(); }
});
async function renderAdvDashboard(root) {
  html(root, `${navbar()}<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="mb-8"><h1 class="text-2xl font-bold text-gray-900">Добро пожаловать, ${state.user.name}</h1><p class="text-gray-600 text-sm mt-1">Управляйте рекламными кампаниями.</p></div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm"><p class="text-sm font-medium text-gray-500">Всего кампаний</p><p class="text-2xl font-bold text-gray-900 mt-1" id="adv-total">—</p></div>
      <div class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm"><p class="text-sm font-medium text-gray-500">На модерации</p><p class="text-2xl font-bold text-yellow-600 mt-1" id="adv-pending">—</p></div>
      <div class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm"><p class="text-sm font-medium text-gray-500">Бюджет / Потрачено</p><p class="text-2xl font-bold text-gray-900 mt-1" id="adv-budget">—</p></div>
    </div>
    <div class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm mb-8">
      <div class="flex items-center justify-between mb-3"><span class="text-sm font-semibold text-gray-700">Баланс рекламодателя</span><span class="text-sm font-bold text-gray-900" id="adv-balance">—</span></div>
      <div class="balance-bar"><div class="balance-fill" id="adv-balance-fill" style="width: 0%"></div></div>
      <p class="text-xs text-gray-500 mt-2">Средства зачисляются после пополнения баланса.</p>
    </div>
    <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center"><h2 class="text-lg font-semibold text-gray-900">Мои кампании</h2><div class="flex gap-2"><button onclick="navigate('#advertiser/create')" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition shadow-md"><i class="fa-solid fa-plus mr-2"></i> Создать кампанию</button><button onclick="navigate('#advertiser/topup')" class="px-4 py-2 border border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg transition">Пополнить баланс</button></div></div>
      <div class="overflow-x-auto"><table class="w-full text-left"><thead class="bg-gray-50"><tr><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">#</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">Название</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">Бюджет</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">Потрачено</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">Статус</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">Создана</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase text-right">Действия</th></tr></thead><tbody id="adv-table-body" class="divide-y divide-gray-100"><tr><td colspan="7" class="px-6 py-8 text-center text-gray-500">Загрузка кампаний…</td></tr></tbody></table></div>
    </div>
  </div>`);

  try {
    const data = await api.getCampaigns();
    state.campaigns = data.campaigns || data || [];
    const my = state.campaigns.filter(c => c.advertiserId === state.user.id);
    const totalBudget = my.reduce((s, c) => s + (c.budget || 0), 0);
    const totalSpent = my.reduce((s, c) => s + (c.spent || 0), 0);
    const pending = my.filter(c => c.status === 'pending').length;

    $('#adv-total').textContent = my.length;
    $('#adv-pending').textContent = pending;
    $('#adv-budget').textContent = `${totalBudget.toLocaleString('ru-RU')} ₽ / ${totalSpent.toLocaleString('ru-RU')} ₽`;
    $('#adv-balance').textContent = `${(state.user.balance || 0).toLocaleString('ru-RU')} ₽`;
    const pct = totalBudget ? Math.min(100, (totalSpent / totalBudget) * 100) : 0;
    $('#adv-balance-fill').style.width = pct + '%';

    const rows = my.map(c => `<tr class="hover:bg-gray-50 transition"><td class="px-6 py-4 text-sm text-gray-900 font-medium">#${c.id}</td><td class="px-6 py-4 text-sm text-gray-900">${escapeHtml(c.title)}</td><td class="px-6 py-4 text-sm text-gray-900">${(c.budget || 0).toLocaleString('ru-RU')} ₽</td><td class="px-6 py-4 text-sm text-gray-900">${(c.spent || 0).toLocaleString('ru-RU')} ₽</td><td class="px-6 py-4"><span class="status-badge status-${c.status}">${c.status === 'pending' ? 'На модерации' : c.status === 'approved' ? 'Одобрена' : 'Отклонена'}</span></td><td class="px-6 py-4 text-sm text-gray-500">${c.createdAt}</td><td class="px-6 py-4 text-sm text-right">${c.status === 'pending' ? `<button onclick="navigate('#advertiser/create?id=${c.id}')" class="text-blue-600 hover:text-blue-800 font-medium">Редактировать</button>` : '<span class="text-gray-400">—</span>'}</td></tr>`).join('') || '<tr><td colspan="7" class="px-6 py-8 text-center text-gray-500">У вас пока нет кампаний. Создайте первую!</td></tr>';
    $('#adv-table-body').innerHTML = rows;
  } catch (e) {
    $('#adv-table-body').innerHTML = '<tr><td colspan="7" class="px-6 py-8 text-center text-red-500">Ошибка загрузки кампаний: ' + escapeHtml(e.message) + '</td></tr>';
  }
}

function renderAdvCreate(root) {
  const params = new URLSearchParams(window.location.hash.split('?')[1] || '');
  const editId = params.get('id');
  const editing = editId ? state.campaigns.find(c => c.id == editId && c.advertiserId === state.user.id) : null;
  const dv = editing || { title: '', description: '', url: '', budget: '' };
  html(root, `
    ${navbar()}
    <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="flex items-center justify-between mb-6"><div><h1 class="text-2xl font-bold text-gray-900">${editing ? 'Редактирование кампании' : 'Создание рекламной кампании'}</h1><p class="text-gray-600 text-sm">${editing ? 'Внесите изменения и отправьте на повторную модерацию.' : 'Заполните форму, чтобы отправить рекламу на проверку модератору.'}</p></div><button onclick="navigate('#advertiser/dashboard')" class="text-gray-500 hover:text-gray-700 text-sm font-medium flex items-center gap-1"><i class="fa-solid fa-arrow-left"></i> Назад</button></div>
      <form id="campaign-form" class="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="col-span-2"><label class="block text-sm font-medium text-gray-700 mb-2">Название кампании *</label><input type="text" id="title" value="${escapeHtml(dv.title)}" required class="w-full px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"></div>
          <div class="col-span-2"><label class="block text-sm font-medium text-gray-700 mb-2">Описание</label><textarea id="description" rows="3" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition">${escapeHtml(dv.description || '')}</textarea></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-2">Ссылка (URL) *</label><input type="url" id="url" value="${escapeHtml(dv.url || '')}" placeholder="https://example.com" required class="w-full px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-2">Бюджет (₽) *</label><input type="number" id="budget" value="${escapeHtml(dv.budget || '')}" min="0" required class="w-full px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"></div>
          <div class="col-span-2"><label class="block text-sm font-medium text-gray-700 mb-2">Медиафайл (изображение / видео)</label><input type="file" id="media" accept="image/*,video/*" class="w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 transition"><div id="media-preview" class="mt-3 h-48 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center overflow-hidden relative media-placeholder"><i class="fa-solid fa-image text-2xl text-gray-400 mb-2"></i><p class="text-sm text-gray-500">Нет выбранного файла</p></div></div>
        </div>
        <div class="flex justify-end gap-3 pt-4 border-t border-gray-100"><button type="button" onclick="navigate('#advertiser/dashboard')" class="px-6 py-2.5 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition">Отмена</button><button type="submit" class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium shadow-md transition"><i class="fa-solid fa-paper-plane mr-2"></i> ${editing ? 'Сохранить изменения' : 'Отправить на модерацию'}</button></div>
      </form>
    </div>
  `);

  const mediaInput = $('#media');
  const preview = $('#media-preview');
  mediaInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    preview.className = 'mt-3 h-48 rounded-lg border-2 border-dashed border-blue-300 flex items-center justify-center overflow-hidden relative';
    preview.innerHTML = '';
    if (file.type.startsWith('video')) {
      preview.innerHTML = `<div class="text-center"><div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-2"><i class="fa-solid fa-play text-blue-600 text-xl"></i></div><p class="text-sm text-gray-700 font-medium">${escapeHtml(file.name)}</p><p class="text-xs text-gray-500">Видео выбрано</p></div>`;
    } else {
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      img.className = 'w-full h-full object-cover';
      preview.appendChild(img);
    }
  });

  const form = $('#campaign-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = $('#title').value.trim();
    const description = $('#description').value.trim();
    const url = $('#url').value.trim();
    const budget = parseInt($('#budget').value, 10) || 0;
    if (!title || !url || !budget) { alert('Заполните обязательные поля.'); return; }

    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('url', url);
    formData.append('budget', String(budget));
    if (mediaInput.files[0]) formData.append('media', mediaInput.files[0]);

    try {
      if (editing) {
        await api.updateCampaign(editing.id, formData);
        alert('Кампания обновлена и отправлена на повторную модерацию.');
      } else {
        await api.createCampaign(formData);
        alert('Кампания отправлена на модерацию.');
      }
      navigate('#advertiser/dashboard');
    } catch (err) {
      alert('Ошибка: ' + err.message);
    }
  });
}

async function renderAdvTopup(root) {
  html(root, `${navbar()}<div class="max-w-lg mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm text-center">
      <div class="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center mx-auto mb-6"><i class="fa-solid fa-wallet text-2xl text-blue-600"></i></div>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Пополнение баланса</h1>
      <p class="text-gray-600 text-sm mb-6">Введите сумму для зачисления на рекламный баланс.</p>
      <div class="space-y-4 mb-8">
        <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-100">
          <span class="text-sm font-medium text-gray-700">Сумма пополнения (₽)</span>
          <input type="number" id="topup-amount" placeholder="0" min="0" class="w-32 px-3 py-2 text-right bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none">
        </div>
      </div>
      <button onclick="doTopup()" id="topup-btn" class="w-full px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-semibold shadow-lg transition">Оплатить</button>
      <p class="mt-6 text-xs text-gray-400">После успешного пополнения средства зачислятся на ваш рекламный баланс.</p>
    </div>
  </div>`);
}

async function doTopup() {
  const amount = parseInt($('#topup-amount').value, 10);
  if (!amount || amount <= 0) { alert('Введите корректную сумму.'); return; }
  const btn = $('#topup-btn');
  const original = btn.innerHTML;
  btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Обработка…';
  btn.disabled = true;
  try {
    await api.topup(amount);
    alert(`Баланс пополнен на ${amount.toLocaleString('ru-RU')} ₽.`);
    navigate('#advertiser/dashboard');
  } catch (err) {
    alert('Ошибка пополнения: ' + err.message);
  } finally {
    btn.innerHTML = original;
    btn.disabled = false;
  }
}

async function renderModDashboard(root) {
  html(root, `${navbar()}<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="flex items-center justify-between mb-6">
      <div><h1 class="text-2xl font-bold text-gray-900">Панель модератора</h1><p class="text-gray-600 text-sm">Модерация рекламных кампаний и коммуникация с рекламодателями.</p></div>
      <div class="flex gap-2">
        <button onclick="setModFilter('all')" class="px-3 py-1.5 text-sm rounded-lg font-medium ${state.modFilter === 'all' ? 'bg-blue-100 text-blue-700' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 transition'}">Все</button>
        <button onclick="setModFilter('pending')" class="px-3 py-1.5 text-sm rounded-lg font-medium ${state.modFilter === 'pending' ? 'bg-yellow-100 text-yellow-700' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 transition'}">На модерации</button>
        <button onclick="setModFilter('approved')" class="px-3 py-1.5 text-sm rounded-lg font-medium ${state.modFilter === 'approved' ? 'bg-green-100 text-green-700' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 transition'}">Одобренные</button>
        <button onclick="setModFilter('rejected')" class="px-3 py-1.5 text-sm rounded-lg font-medium ${state.modFilter === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 transition'}">Отклонённые</button>
      </div>
    </div>
    <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
      <div class="overflow-x-auto"><table class="w-full text-left"><thead class="bg-gray-50 sticky top-0 z-10"><tr><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">#</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">Рекламодатель</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">Кампания</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">Бюджет</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">Статус</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase">Создана</th><th class="px-6 py-3 text-sm font-semibold text-gray-500 uppercase text-right">Действие</th></tr></thead><tbody id="mod-table-body" class="divide-y divide-gray-100"><tr><td colspan="7" class="px-6 py-8 text-center text-gray-500">Загрузка заявок…</td></tr></tbody></table></div>
    </div>
  </div>`);

  try {
    const data = await api.getCampaigns({ status: state.modFilter === 'all' ? undefined : state.modFilter });
    state.campaigns = data.campaigns || data || [];
    const filtered = state.modFilter === 'all' ? state.campaigns : state.campaigns.filter(c => c.status === state.modFilter);

    const rows = filtered.map(c => `<tr class="hover:bg-gray-50 transition group"><td class="px-6 py-4 text-sm text-gray-900 font-medium">#${c.id}</td><td class="px-6 py-4 text-sm text-gray-900">${escapeHtml(c.advertiserName || c.advertiser?.name || '—')}</td><td class="px-6 py-4 text-sm text-gray-900">${escapeHtml(c.title)}</td><td class="px-6 py-4 text-sm text-gray-900">${(c.budget || 0).toLocaleString('ru-RU')} ₽</td><td class="px-6 py-4"><span class="status-badge status-${c.status}">${c.status === 'pending' ? 'На модерации' : c.status === 'approved' ? 'Одобрена' : 'Отклонена'}</span></td><td class="px-6 py-4 text-sm text-gray-500">${c.createdAt}</td><td class="px-6 py-4 text-sm text-right"><button onclick="state.currentCampaignId='${c.id}'; navigate('#moderator/campaign')" class="text-blue-600 hover:text-blue-800 font-medium">Посмотреть</button></td></tr>`).join('') || '<tr><td colspan="7" class="px-6 py-8 text-center text-gray-500">Кампаний по выбранному фильтру нет.</td></tr>';
    $('#mod-table-body').innerHTML = rows;
  } catch (e) {
    $('#mod-table-body').innerHTML = '<tr><td colspan="7" class="px-6 py-8 text-center text-red-500">Ошибка загрузки заявок: ' + escapeHtml(e.message) + '</td></tr>';
  }
}

window.setModFilter = (f) => { state.modFilter = f; router(); };

async function renderModCampaign(root) {
  if (!state.currentCampaignId) { html(root, '<div class="p-8 text-center text-gray-500">Кампания не выбрана.</div>'); return; }
  let c;
  try {
    c = await api.getCampaign(state.currentCampaignId);
  } catch (e) {
    html(root, `<div class="p-8 text-center text-red-500">Ошибка загрузки кампании: ${escapeHtml(e.message)}</div>`);
    return;
  }
  const statusLabel = c.status === 'pending' ? 'На модерации' : c.status === 'approved' ? 'Одобрена' : 'Отклонена';
  const mediaHtml = c.mediaUrl ? (c.mediaType === 'image' ? `<img src="${c.mediaUrl}" class="w-full h-48 object-cover rounded-lg border border-gray-200">` : `<div class="w-full h-48 bg-gray-100 rounded-lg border border-gray-200 flex items-center justify-center"><i class="fa-solid fa-play text-gray-400 text-2xl"></i><span class="text-gray-500 ml-2">Видео</span></div>`) : `<div class="w-full h-48 media-placeholder rounded-lg border border-gray-200 flex items-center justify-center"><i class="fa-solid fa-image text-gray-400 text-xl"></i><span class="text-gray-500 ml-2">Медиа не загружено</span></div>`;
  html(root, `
    ${navbar()}
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <button onclick="navigate('#moderator/dashboard')" class="mb-6 text-gray-500 hover:text-gray-700 text-sm font-medium flex items-center gap-1"><i class="fa-solid fa-arrow-left"></i> К списку заявок</button>
      <div class="mod-card p-6 md:p-8">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="lg:col-span-2 space-y-6">
            <div class="flex justify-between items-start"><div><h2 class="text-xl font-bold text-gray-900 mb-1">${escapeHtml(c.title)}</h2><p class="text-sm text-gray-500">Рекламодатель: ${escapeHtml(c.advertiserName || c.advertiser?.name || '—')}</p></div><span class="status-badge status-${c.status}">${statusLabel}</span></div>
            <div class="border rounded-xl border-gray-200 overflow-hidden">${mediaHtml}</div>
            <div class="space-y-2"><p class="text-sm font-medium text-gray-700">Описание</p><p class="text-gray-600">${escapeHtml(c.description || '—')}</p></div>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div class="p-3 bg-gray-50 rounded-lg"><p class="text-xs text-gray-500 uppercase">Бюджет</p><p class="font-semibold text-gray-900">${(c.budget || 0).toLocaleString('ru-RU')} ₽</p></div>
              <div class="p-3 bg-gray-50 rounded-lg"><p class="text-xs text-gray-500 uppercase">Потрачено</p><p class="font-semibold text-gray-900">${(c.spent || 0).toLocaleString('ru-RU')} ₽</p></div>
              <div class="p-3 bg-gray-50 rounded-lg"><p class="text-xs text-gray-500 uppercase">Показы</p><p class="font-semibold text-gray-900">${(c.impressions || 0).toLocaleString('ru-RU')}</p></div>
              <div class="p-3 bg-gray-50 rounded-lg"><p class="text-xs text-gray-500 uppercase">Клики</p><p class="font-semibold text-gray-900">${(c.clicks || 0).toLocaleString('ru-RU')}</p></div>
              <div class="p-3 bg-gray-50 rounded-lg"><p class="text-xs text-gray-500 uppercase">Ссылка</p><a href="${c.url}" target="_blank" class="text-blue-600 hover:underline truncate">${c.url}</a></div>
              <div class="p-3 bg-gray-50 rounded-lg"><p class="text-xs text-gray-500 uppercase">Создана</p><p class="font-semibold text-gray-900">${c.createdAt}</p></div>
            </div>
          </div>
          <div class="lg:col-span-1 space-y-4">
            <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <h3 class="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2"><i class="fa-solid fa-comment-dots text-indigo-500"></i> Комментарий модератора</h3>
              <textarea id="mod-comment" rows="4" placeholder="Напишите комментарий для рекламодателя…${c.moderatorComment ? '\n\nТекущий: ' + c.moderatorComment : ''}" class="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none text-sm">${c.moderatorComment || ''}</textarea>
              <p class="text-xs text-gray-500 mt-1">Комментарий увидит рекламодатель при одобрении или отказе.</p>
            </div>
            <div class="space-y-3">
              <button onclick="moderate('approved')" class="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-semibold shadow-md transition flex items-center justify-center gap-2"><i class="fa-solid fa-check"></i> Одобрить</button>
              <button onclick="moderate('rejected')" class="w-full py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-semibold shadow-md transition flex items-center justify-center gap-2"><i class="fa-solid fa-times"></i> Отклонить</button>
            </div>
            ${c.status !== 'pending' ? `<div class="p-3 bg-gray-50 rounded-lg border border-gray-100"><p class="text-xs text-gray-500 uppercase mb-1">Решение уже принято</p><p class="text-sm text-gray-700">${c.moderatorComment || 'Без комментария'}</p></div>` : ''}
          </div>
        </div>
      </div>
    </div>
  `);
}

window.moderate = async (status) => {
  if (!state.currentCampaignId) return;
  const comment = $('#mod-comment').value.trim();
  if (!comment && status === 'rejected') {
    if (!confirm('Вы уверены, что хотите отклонить без комментария? Рекламодатель не узнает причину.')) return;
  }
  try {
    await api.moderateCampaign(state.currentCampaignId, { status, comment });
    alert(status === 'approved' ? 'Кампания одобрена.' : 'Кампания отклонена.');
    navigate('#moderator/dashboard');
  } catch (err) {
    alert('Ошибка модерации: ' + err.message);
  }
};

