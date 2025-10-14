# CopyKit Data Fetching Implementation

This document describes the data fetching functionality implemented for the CopyKit project, which allows the React frontend to dynamically fetch data from the CopyKit URL (`https://copykit-gv4rmq.manus.space`).

## Overview

The implementation provides a complete data fetching solution that:
- Fetches data from the CopyKit URL
- Parses HTML content to extract relevant information
- Provides API endpoints for the React frontend
- Includes error handling and fallback mechanisms
- Supports real-time analytics and product data

## Architecture

```
CopyKit URL (https://copykit-gv4rmq.manus.space)
    ↓ (HTTP Request)
Flask API (/api/copykit/*)
    ↓ (JSON Response)
React Frontend (useCopyKitData hooks)
    ↓ (State Management)
UI Components (Dynamic rendering)
```

## API Endpoints

### 1. `/api/copykit/data` (GET)
Fetches and parses data from the CopyKit URL.

**Response:**
```json
{
  "status": "success",
  "data": {
    "global_env": {
      "apiHost": "https://api.manus.im",
      "host": "https://manus.im",
      "amplitudeKey": "46ac3f9abb41dd2d17a5785e052bc6d3"
    },
    "title": "CopyKit - AI-Powered Copywriting That Converts",
    "meta_description": "<meta name=\"description\" content=\"...\">",
    "last_updated": "2025-10-14T17:00:30.432395"
  }
}
```

### 2. `/api/copykit/products` (GET)
Returns product data from the database with real-time pricing.

**Response:**
```json
{
  "status": "success",
  "products": [
    {
      "id": "monthly",
      "name": "CopyKit Monthly",
      "price": "£49",
      "period": "/month",
      "sku": "COPYKIT-MONTHLY",
      "description": "Perfect for growing businesses",
      "features": ["Weekly ad creative packs", "..."],
      "popular": true,
      "available": true
    }
  ]
}
```

### 3. `/api/copykit/analytics` (GET)
Returns analytics and performance data.

**Response:**
```json
{
  "status": "success",
  "analytics": {
    "totals": {
      "visitors": 1250,
      "leads": 89,
      "orders": 23,
      "revenue": 3450.00
    },
    "recent_orders": [...],
    "kpi_trend": [...]
  }
}
```

## React Integration

### Custom Hooks

#### `useCopyKitData()`
Fetches general data from the CopyKit URL.

```javascript
import { useCopyKitData } from './hooks/useCopyKitData';

function MyComponent() {
  const { data, loading, error } = useCopyKitData();
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return <div>{data?.title}</div>;
}
```

#### `useProducts()`
Fetches product data with fallback to hardcoded products.

```javascript
import { useProducts } from './hooks/useCopyKitData';

function PricingSection() {
  const { products, loading, error } = useProducts();
  
  return (
    <div>
      {products.map(product => (
        <div key={product.id}>
          <h3>{product.name}</h3>
          <p>{product.price}{product.period}</p>
        </div>
      ))}
    </div>
  );
}
```

#### `useAnalytics()`
Fetches analytics data for display.

```javascript
import { useAnalytics } from './hooks/useCopyKitData';

function AnalyticsDisplay() {
  const { analytics, loading } = useAnalytics();
  
  if (loading) return <div>Loading analytics...</div>;
  
  return (
    <div>
      <p>Total Orders: {analytics?.totals?.orders}</p>
      <p>Revenue: £{analytics?.totals?.revenue}</p>
    </div>
  );
}
```

### API Service

The `copyKitAPI` service provides a centralized way to make API calls:

```javascript
import copyKitAPI from './services/api';

// Fetch CopyKit data
const data = await copyKitAPI.getCopyKitData();

// Fetch products
const products = await copyKitAPI.getProducts();

// Create a lead
const lead = await copyKitAPI.createLead({
  email: 'user@example.com',
  name: 'John Doe'
});
```

## Features

### 1. Dynamic Data Loading
- Products are loaded from the database
- Real-time pricing and availability
- Fallback to hardcoded data if API fails

### 2. Loading States
- Skeleton loading animations
- Error handling with user-friendly messages
- Graceful degradation

### 3. Analytics Integration
- Real-time metrics display
- Revenue and order tracking
- Performance indicators

### 4. Error Handling
- Network error recovery
- API error fallbacks
- User-friendly error messages

## Configuration

### Environment Variables

Create a `.env` file in the React app root:

```env
# API Configuration
REACT_APP_API_URL=http://localhost:5000

# CopyKit URL
REACT_APP_COPYKIT_URL=https://copykit-gv4rmq.manus.space

# Feature Flags
REACT_APP_ENABLE_DYNAMIC_PRICING=true
REACT_APP_ENABLE_ANALYTICS_DISPLAY=true
REACT_APP_ENABLE_REAL_TIME_DATA=true
```

### Dependencies

**Backend (Flask API):**
```
flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
beautifulsoup4==4.12.2
prisma==0.11.0
```

**Frontend (React):**
```json
{
  "react": "^19.1.0",
  "react-dom": "^19.1.0"
}
```

## Testing

### Test Scripts

1. **Basic URL Test:**
   ```bash
   python3 test_copykit_data.py
   ```

2. **Demonstration:**
   ```bash
   python3 demo_copykit_fetch.py
   ```

### Manual Testing

1. Start the Flask API:
   ```bash
   cd /workspace
   python3 api/app.py
   ```

2. Start the React app:
   ```bash
   cd /workspace/web/copykit-landing
   pnpm install
   pnpm run dev
   ```

3. Visit `http://localhost:5173` to see the dynamic data loading

## Error Scenarios

### 1. CopyKit URL Unavailable
- Falls back to hardcoded product data
- Shows error message to user
- Continues to function normally

### 2. API Server Down
- React app uses fallback data
- Loading states indicate issues
- User experience remains smooth

### 3. Database Connection Issues
- API returns error responses
- Frontend handles gracefully
- Fallback mechanisms activate

## Performance Considerations

### 1. Caching
- API responses can be cached
- React Query could be added for advanced caching
- Static data served from CDN

### 2. Loading Optimization
- Skeleton screens for better UX
- Progressive loading of components
- Lazy loading for non-critical data

### 3. Error Recovery
- Automatic retry mechanisms
- Exponential backoff for failed requests
- User-initiated refresh options

## Future Enhancements

### 1. Real-time Updates
- WebSocket connections for live data
- Server-sent events for updates
- Push notifications for changes

### 2. Advanced Analytics
- Real-time dashboard
- Historical data visualization
- Predictive analytics

### 3. A/B Testing
- Dynamic content variations
- User behavior tracking
- Conversion optimization

## Troubleshooting

### Common Issues

1. **CORS Errors:**
   - Ensure Flask-CORS is properly configured
   - Check API URL configuration

2. **Data Not Loading:**
   - Verify CopyKit URL is accessible
   - Check API server status
   - Review browser console for errors

3. **Styling Issues:**
   - Ensure Tailwind CSS is properly loaded
   - Check component imports
   - Verify responsive design classes

### Debug Mode

Enable debug logging in the React app:

```javascript
// In services/api.js
const DEBUG = process.env.NODE_ENV === 'development';

if (DEBUG) {
  console.log('API Request:', endpoint, options);
}
```

## Conclusion

The CopyKit data fetching implementation provides a robust, scalable solution for dynamic content loading. It includes comprehensive error handling, loading states, and fallback mechanisms to ensure a smooth user experience even when external services are unavailable.

The modular architecture makes it easy to extend with additional data sources and features, while the React hooks provide a clean, reusable interface for components to access dynamic data.