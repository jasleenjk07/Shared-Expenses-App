const API = '/api';

function getToken() {
  return localStorage.getItem('token');
}

async function request(path, options = {}) {
  const headers = { ...options.headers };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

export const api = {
  login: (email, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (email, password, name) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ email, password, name }) }),
  me: () => request('/auth/me'),
  getGroups: () => request('/groups'),
  createGroup: (data) => request('/groups', { method: 'POST', body: JSON.stringify(data) }),
  getGroup: (id) => request(`/groups/${id}`),
  getExpenses: (groupId) => request(`/groups/${groupId}/expenses`),
  getBalances: (groupId) => request(`/groups/${groupId}/balances`),
  getMemberBreakdown: (groupId, userId) => request(`/groups/${groupId}/balances/${userId}`),
  getSettlements: (groupId) => request(`/groups/${groupId}/settlements`),
  addSettlement: (groupId, data) =>
    request(`/groups/${groupId}/settlements`, { method: 'POST', body: JSON.stringify(data) }),
  importCsv: (groupId, file) => {
    const form = new FormData();
    form.append('file', file);
    return request(`/groups/${groupId}/import`, { method: 'POST', body: form });
  },
  getImportSessions: (groupId) => request(`/groups/${groupId}/import/sessions`),
  getImportReport: (groupId, sessionId) =>
    request(`/groups/${groupId}/import/sessions/${sessionId}`),
  getGroupUsers: (groupId) => request(`/groups/${groupId}/users`),
};

export function formatINR(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(amount);
}
