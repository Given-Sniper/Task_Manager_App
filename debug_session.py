#!/usr/bin/env python3
"""
Debug session data
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def debug_pm_session():
    """Debug project manager session"""
    print("=== Debugging PM Session ===")
    
    session = requests.Session()
    
    # Login with emp_id
    login_data = {
        'emp_id': 'PM001',
        'password': 'manager123'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    print(f"Login status: {response.status_code}")
    print(f"Login response: {response.text[:200]}...")
    
    # Check what's in session by accessing a protected endpoint
    response = session.get(f"{BASE_URL}/pending_review_tasks")
    print(f"Pending review tasks status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Try another protected endpoint to compare
    response = session.get(f"{BASE_URL}/project_manager_dashboard")
    print(f"PM dashboard status: {response.status_code}")

if __name__ == "__main__":
    debug_pm_session()