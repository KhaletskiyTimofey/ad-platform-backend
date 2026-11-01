const BASE_URL = 'http://localhost:3000/api';

async function apiRequest(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {};
  const token = localStorage.getItem('adplatform_token');
  if (token) headers.Authorization = `Bearer ${token}`;

  let body = options.body;
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    if (typeof body === 'object') body = JSON.stringify(body);
  }

  try {
    const res = await fetch(url, { ...options, headers, body });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || `Ошибка ${res.status}`);
    }
    if (res.status === 204) return null;
    return res.json();
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Бэкенд недоступен. Убедитесь, что сервер запущен на ' + BASE_URL);
    }
    throw err;
  }
}

const api = {
  async login(role) {
    return apiRequest('/auth/login', { method: 'POST', body: { role } });
  },
  async logout() {
    return apiRequest('/auth/logout', { method: 'POST' });
  },
  async me() {
    return apiRequest('/auth/me');
  },
  async getCampaigns(filter = {}) {
    const qs = new URLSearchParams(filter).toString();
    return apiRequest(`/campaigns?${qs}`);
  },
  async getCampaign(id) {
    return apiRequest(`/campaigns/${id}`);
  },
  async createCampaign(formData) {
    return apiRequest('/campaigns', { method: 'POST', body: formData });
  },
  async updateCampaign(id, formData) {
    return apiRequest(`/campaigns/${id}`, { method: 'PUT', body: formData });
  },
  async moderateCampaign(id, { status, comment }) {
    return apiRequest(`/campaigns/${id}/moderate`, {
      method: 'POST',
      body: { status, comment },
    });
  },
  async topup(amount) {
    return apiRequest('/balance/topup', { method: 'POST', body: { amount } });
  },
  async stats() {
    return apiRequest('/stats');
  },
};

window.api = api;