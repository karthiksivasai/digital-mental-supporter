#!/usr/bin/env python3
"""
Quick test script to verify login endpoint works
"""
import requests
import sys

def test_login():
    url = "http://localhost:8000/api/auth/login"
    
    # Test data - replace with your actual credentials
    test_data = {
        "username": "test@example.com",  # Replace with your email
        "password": "testpassword"  # Replace with your password
    }
    
    print("Testing login endpoint...")
    print(f"URL: {url}")
    print(f"Data: {test_data['username']}")
    
    try:
        response = requests.post(
            url,
            data=test_data,
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("\n✅ Login successful!")
            data = response.json()
            print(f"Token: {data.get('access_token', 'N/A')[:50]}...")
            return True
        else:
            print(f"\n❌ Login failed: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server!")
        print("   → Is the backend server running?")
        print("   → Start it with: uvicorn app.main:app --reload")
        return False
    except requests.exceptions.Timeout:
        print("\n❌ ERROR: Request timed out!")
        print("   → Server might be hung or not responding")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def test_health():
    """Test if server is running"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is NOT running!")
        print("   Start it with: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Login Endpoint Test")
    print("=" * 50)
    
    # First check if server is running
    print("\n1. Checking if server is running...")
    if not test_health():
        sys.exit(1)
    
    # Then test login
    print("\n2. Testing login endpoint...")
    print("   (Update credentials in this script if needed)")
    test_login()
    
    print("\n" + "=" * 50)

