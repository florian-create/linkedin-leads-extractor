import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/');
    return response.data;
  },

  // Accounts
  getAccounts: async () => {
    const response = await api.get('/api/accounts');
    return response.data;
  },

  // Posts
  extractLeads: async (postUrl, accountId = null, enrich = false) => {
    const response = await api.post('/api/posts/extract', {
      post_url: postUrl,
      account_id: accountId,
      enrich: enrich,
    });
    return response.data;
  },

  getPosts: async (skip = 0, limit = 20, status = null) => {
    const params = { skip, limit };
    if (status) params.status = status;

    const response = await api.get('/api/posts', { params });
    return response.data;
  },

  getPost: async (postId) => {
    const response = await api.get(`/api/posts/${postId}`);
    return response.data;
  },

  deletePost: async (postId) => {
    const response = await api.delete(`/api/posts/${postId}`);
    return response.data;
  },

  // Leads
  getPostLeads: async (postId, skip = 0, limit = 100, interactionType = null) => {
    const params = { skip, limit };
    if (interactionType) params.interaction_type = interactionType;

    const response = await api.get(`/api/posts/${postId}/leads`, { params });
    return response.data;
  },

  enrichLeads: async (postId) => {
    const response = await api.post(`/api/posts/${postId}/enrich`);
    return response.data;
  },

  // Export
  exportLeadsCSV: (postId) => {
    return `${API_BASE_URL}/api/posts/${postId}/export/csv`;
  },

  exportLeadsExcel: (postId) => {
    return `${API_BASE_URL}/api/posts/${postId}/export/excel`;
  },

  // Stats
  getStats: async () => {
    const response = await api.get('/api/stats');
    return response.data;
  },
};

export default apiService;
