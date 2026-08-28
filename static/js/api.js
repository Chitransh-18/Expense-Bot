const API = {
  getToken() {
    return localStorage.getItem('token');
  },

  setToken(token) {
    localStorage.setItem('token', token);
  },

  clearToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
  },

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      ...options.headers
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(endpoint, {
        cache: 'no-store',
        ...options,
        headers
      });

      if (response.status === 401) {
        this.clearToken();
        if (window.location.hash !== '#auth') {
          window.location.hash = '#auth';
        }
        return { error: 'Session expired. Please log in again.' };
      }

      const contentType = response.headers.get('content-type') || '';
      let data = {};

      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        console.warn('Non-JSON response received:', text);
        if (!response.ok) {
          throw new Error('Server is initializing or updating. Please try again in a moment.');
        }
        return { message: text };
      }

      if (!response.ok) {
        throw new Error(data.error || 'API Request failed');
      }
      return data;
    } catch (err) {
      console.error('API Error:', err);
      throw err;
    }
  }
};
