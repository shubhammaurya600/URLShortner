import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
});

export const urlApi = {
    /**
     * POST /api/v1/shorten/
     */
    shorten: (payload) => api.post('/api/v1/shorten/', payload),

    /**
     * GET /api/v1/<short_code>/analytics/
     */
    analytics: (shortCode) => api.get(`/api/v1/${shortCode}/analytics/`),

    /**
     * GET /health/
     */
    health: () => api.get('/health/'),

    /**
     * Returns the qrcode URL (static, we display as <img>)
     */
    qrcodeUrl: (shortCode) => `${API_BASE}/api/v1/${shortCode}/qrcode/`,

    /**
     * Returns the redirect URL
     */
    redirectUrl: (shortCode) => `${API_BASE}/api/v1/${shortCode}/redirect/`,
};

export default api;
