#!/usr/bin/env python3
"""
Test script for CopyKit data fetching functionality
"""

import requests
import json
import sys
from datetime import datetime

def test_copykit_url():
    """Test fetching data from CopyKit URL"""
    print("🔍 Testing CopyKit URL data fetching...")
    
    try:
        response = requests.get('https://copykit-gv4rmq.manus.space', timeout=10)
        response.raise_for_status()
        
        print(f"✅ CopyKit URL accessible (Status: {response.status_code})")
        print(f"📄 Content length: {len(response.text)} characters")
        
        # Check for global environment variables
        if '__manus__global_env' in response.text:
            print("✅ Global environment variables found in response")
        else:
            print("⚠️  Global environment variables not found")
            
        return True
        
    except requests.RequestException as e:
        print(f"❌ Error fetching CopyKit URL: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints (if running locally)"""
    print("\n🔍 Testing API endpoints...")
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/health",
        "/api/copykit/data",
        "/api/copykit/products",
        "/api/copykit/analytics"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"⚠️  {endpoint} - Status {response.status_code}")
        except requests.ConnectionError:
            print(f"❌ {endpoint} - Connection failed (API not running?)")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def test_data_parsing():
    """Test parsing CopyKit data"""
    print("\n🔍 Testing data parsing...")
    
    try:
        response = requests.get('https://copykit-gv4rmq.manus.space', timeout=10)
        response.raise_for_status()
        
        # Simple parsing test
        if 'CopyKit' in response.text:
            print("✅ CopyKit branding found in response")
        else:
            print("⚠️  CopyKit branding not found")
            
        if 'React' in response.text or 'react' in response.text:
            print("✅ React application detected")
        else:
            print("⚠️  React application not detected")
            
        return True
        
    except Exception as e:
        print(f"❌ Error parsing data: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 CopyKit Data Fetching Test Suite")
    print("=" * 50)
    
    # Test CopyKit URL
    url_success = test_copykit_url()
    
    # Test data parsing
    parse_success = test_data_parsing()
    
    # Test API endpoints (optional)
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"CopyKit URL: {'✅ PASS' if url_success else '❌ FAIL'}")
    print(f"Data Parsing: {'✅ PASS' if parse_success else '❌ FAIL'}")
    print("API Endpoints: Check individual results above")
    
    if url_success and parse_success:
        print("\n🎉 All core tests passed! CopyKit data fetching is working.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())