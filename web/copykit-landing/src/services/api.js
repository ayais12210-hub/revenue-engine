// API service for CopyKit data fetching
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class CopyKitAPI {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Fetch CopyKit URL data
  async getCopyKitData() {
    return this.request('/api/copykit/data');
  }

  // Fetch products from database
  async getProducts() {
    return this.request('/api/copykit/products');
  }

  // Fetch analytics data
  async getAnalytics() {
    return this.request('/api/copykit/analytics');
  }

  // Create a lead
  async createLead(leadData) {
    return this.request('/api/leads', {
      method: 'POST',
      body: JSON.stringify(leadData),
    });
  }

  // Get daily KPIs
  async getDailyKPIs(days = 30) {
    return this.request(`/api/kpi/daily?days=${days}`);
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }
}

// Create and export a singleton instance
const copyKitAPI = new CopyKitAPI();
export default copyKitAPI;