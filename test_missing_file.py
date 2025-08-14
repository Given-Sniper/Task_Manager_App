#!/usr/bin/env python3
"""
Quick test for missing file validation
"""

import requests
from datetime import datetime

BASE_URL = "http://localhost:5000"

def login_as_pm():
    """Login as Project Manager"""
    session = requests.Session()
    session.get(BASE_URL)
    session.get(f"{BASE_URL}/select_role/project_manager")
    
    login_data = {'emp_id': 'PM001', 'password': 'manager123'}
    response = session.post(f"{BASE_URL}/login", data=login_data)
    return session, response.status_code

def test_missing_file():
    """Test missing file rejection"""
    print("=== Testing Missing File Rejection ===")
    
    session, login_status = login_as_pm()
    if login_status not in [200, 302]:
        print(f"[FAIL] Could not login as PM: {login_status}")
        return False
    
    task_data = {
        'task_id': f"NO_FILE_TEST_{int(datetime.now().timestamp())}",
        'title': 'No File Test',
        'description': 'Testing missing file rejection',
        'project_type': 'web_development',
        'complexity': 'medium',
        'priority': 'medium'
    }
    
    # Test 1: Submit as JSON (should fail - no multipart)
    print("\n1. Testing JSON submission (no file)")
    response = session.post(f"{BASE_URL}/api/create_task", json=task_data)
    print(f"Status: {response.status_code}")
    if response.status_code in [400, 500]:
        result = response.json()
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Test 2: Submit as form data without file (should fail)
    print("\n2. Testing form data submission (no file)")
    response = session.post(f"{BASE_URL}/api/create_task", data=task_data)
    print(f"Status: {response.status_code}")
    if response.status_code in [400, 500]:
        result = response.json()
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Test 3: Submit as multipart with empty file field
    print("\n3. Testing multipart with empty file field")
    files = {'spec_file': ('', '')}  # Empty filename
    response = session.post(f"{BASE_URL}/api/create_task", data=task_data, files=files)
    print(f"Status: {response.status_code}")
    if response.status_code in [400, 500]:
        result = response.json()
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_missing_file()