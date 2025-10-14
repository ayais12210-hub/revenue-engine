#!/usr/bin/env python3
"""
Demonstration of CopyKit data fetching functionality
This script shows how the API endpoints work with the CopyKit URL
"""

import requests
import json
import sys
import os
from datetime import datetime

# Add the api directory to the Python path so we can import the utility
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))
from utils.copykit_parser import parse_copykit_html

def fetch_copykit_data():
    """Fetch and parse data from CopyKit URL"""
    print("🔍 Fetching data from CopyKit URL...")
    
    try:
        response = requests.get('https://copykit-gv4rmq.manus.space', timeout=10)
        response.raise_for_status()
        
        # Parse HTML using the shared utility
        parsed_data = parse_copykit_html(response.text)
        
        # Check if parsing was successful
        if 'error' in parsed_data:
            return {
                'status': 'error',
                'error': parsed_data['error']
            }
        
        return {
            'status': 'success',
            'data': {
                'global_env': parsed_data['global_env'],
                'title': parsed_data['title'] or 'CopyKit - AI-Powered Copywriting That Converts',
                'meta_description': parsed_data['meta_description'],
                'last_updated': datetime.utcnow().isoformat(),
                'content_length': parsed_data['content_length']
            }
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def demonstrate_api_response():
    """Demonstrate what the API would return"""
    print("\n📊 CopyKit Data Fetching Demonstration")
    print("=" * 60)
    
    # Fetch data
    result = fetch_copykit_data()
    
    if result['status'] == 'success':
        print("✅ Successfully fetched data from CopyKit URL")
        print(f"📄 Content length: {result['data']['content_length']} characters")
        print(f"📝 Title: {result['data']['title']}")
        
        if result['data']['global_env']:
            print("\n🌍 Global Environment Variables:")
            for key, value in result['data']['global_env'].items():
                print(f"  {key}: {value}")
        else:
            print("\n⚠️  No global environment variables found")
            
        print(f"\n🕒 Last updated: {result['data']['last_updated']}")
        
        # Show what the API endpoint would return
        print("\n📡 API Response Structure:")
        print(json.dumps({
            'status': 'success',
            'data': {
                'global_env': result['data']['global_env'],
                'title': result['data']['title'],
                'last_updated': result['data']['last_updated']
            }
        }, indent=2))
        
    else:
        print(f"❌ Error fetching data: {result['error']}")

def show_react_integration():
    """Show how the React app would use this data"""
    print("\n⚛️  React Integration Example:")
    print("=" * 60)
    
    print("""
// In your React component:
import { useCopyKitData } from './hooks/useCopyKitData';

function App() {
  const { data, loading, error } = useCopyKitData();
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      <h1>{data?.title}</h1>
      <p>API Host: {data?.global_env?.apiHost}</p>
      <p>Last Updated: {data?.last_updated}</p>
    </div>
  );
}
    """)

def main():
    """Run the demonstration"""
    demonstrate_api_response()
    show_react_integration()
    
    print("\n🎉 Demonstration complete!")
    print("\nNext steps:")
    print("1. Start the Flask API: python api/app.py")
    print("2. Start the React app: cd web/copykit-landing && pnpm run dev")
    print("3. The React app will automatically fetch data from the CopyKit URL")

if __name__ == "__main__":
    main()