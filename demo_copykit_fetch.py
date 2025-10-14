#!/usr/bin/env python3
"""
Demonstration of CopyKit data fetching functionality
This script shows how the API endpoints work with the CopyKit URL
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_copykit_data():
    """Fetch and parse data from CopyKit URL"""
    print("🔍 Fetching data from CopyKit URL...")
    
    try:
        response = requests.get('https://copykit-gv4rmq.manus.space', timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract global environment variables
        script_tags = soup.find_all('script')
        global_env = {}
        
        for script in script_tags:
            if script.string and '__manus__global_env' in script.string:
                # Extract the global environment object
                env_match = re.search(r'__manus__global_env\s*=\s*({[^}]+})', script.string)
                if env_match:
                    try:
                        global_env = json.loads(env_match.group(1))
                    except json.JSONDecodeError:
                        pass
                break
        
        # Extract metadata
        title = soup.title.string if soup.title else 'CopyKit - AI-Powered Copywriting That Converts'
        meta_description = soup.find('meta', attrs={'name': 'description'})
        
        return {
            'status': 'success',
            'data': {
                'global_env': global_env,
                'title': title,
                'meta_description': str(meta_description) if meta_description else None,
                'last_updated': datetime.utcnow().isoformat(),
                'content_length': len(response.text)
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