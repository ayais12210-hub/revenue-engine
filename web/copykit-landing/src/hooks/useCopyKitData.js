import { useState, useEffect } from 'react';
import copyKitAPI from '../services/api';

export const useCopyKitData = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await copyKitAPI.getCopyKitData();
        setData(response.data);
        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching CopyKit data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};

export const useProducts = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        const response = await copyKitAPI.getProducts();
        setProducts(response.products || []);
        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching products:', err);
        // Fallback to hardcoded products if API fails
        setProducts(getDefaultProducts());
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  return { products, loading, error };
};

export const useAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const response = await copyKitAPI.getAnalytics();
        setAnalytics(response.analytics);
        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching analytics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  return { analytics, loading, error };
};

// Default products fallback
const getDefaultProducts = () => [
  {
    id: 'monthly',
    name: 'CopyKit Monthly',
    price: '£49',
    period: '/month',
    sku: 'COPYKIT-MONTHLY',
    description: 'Perfect for growing businesses',
    features: [
      'Weekly ad creative packs (10+ variants)',
      'Monthly landing page copy',
      'Email swipe files',
      'A/B testing variants',
      'Priority support',
      'Brand voice customization'
    ],
    popular: true,
    available: true
  },
  {
    id: 'bundle',
    name: 'Full Funnel Pack',
    price: '£199',
    period: 'one-time',
    sku: 'COPYKIT-BUNDLE',
    description: 'Complete funnel in one package',
    features: [
      'Complete funnel copy (awareness → conversion)',
      '50+ ad creatives',
      '5 landing pages',
      '3 email sequences',
      'Competitor analysis',
      'Lifetime access'
    ],
    popular: false,
    available: true
  },
  {
    id: 'briefing',
    name: 'Daily Briefing',
    price: '£15',
    period: '/month',
    sku: 'DAILYBRIEF-MONTHLY',
    description: 'Stay ahead of market trends',
    features: [
      'Daily market insights',
      'Trend analysis',
      'Audio briefing (TTS)',
      'Social media clips',
      'Trading & creator niches',
      'Archive access'
    ],
    popular: false,
    available: true
  }
];