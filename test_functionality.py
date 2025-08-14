#!/usr/bin/env python3
"""
Test script to verify all the fixed functionality
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_admin_employee_creation():
    """Test admin employee creation functionality"""
    print("\n=== Testing Admin Employee Creation ===")
    
    # Login as admin
    session = requests.Session()
    
    # First select role
    response = session.post(f"{BASE_URL}/select_role", data={'role': 'admin'})
    print(f"Role selection status: {response.status_code}")
    
    # Then login with emp_id
    login_data = {
        'emp_id': 'ADMIN001',  # Use emp_id instead of email
        'password': 'admin123'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    print(f"Admin login status: {response.status_code}")
    
    if response.status_code in [200, 302]:
        # Try to create employee
        employee_data = {
            'name': 'Test Employee',
            'email': 'test@example.com',
            'role': 'developer',
            'experience': '3',
            'password': 'testpass123',
            'skills': 'Python,JavaScript'
        }
        
        response = session.post(f"{BASE_URL}/admin/create_employee", data=employee_data)
        print(f"Employee creation status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response content: {response.text[:200]}...")
        
        return response.status_code in [200, 302]  # 302 is redirect (success)
    
    return False

def test_pending_review_tasks():
    """Test pending review tasks for project manager"""
    print("\n=== Testing Pending Review Tasks ===")
    
    # Login as project manager
    session = requests.Session()
    
    # First select role
    response = session.post(f"{BASE_URL}/select_role", data={'role': 'project_manager'})
    print(f"Role selection status: {response.status_code}")
    
    login_data = {
        'emp_id': 'PM001',  # Use emp_id instead of email
        'password': 'manager123'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    print(f"PM login status: {response.status_code}")
    
    if response.status_code in [200, 302]:
        # Test the pending review tasks endpoint
        response = session.get(f"{BASE_URL}/pending_review_tasks")
        print(f"Pending review tasks status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                return data.get('success', False)
            except:
                print(f"Response text: {response.text}")
                return False
    
    return False

def test_task_approval():
    """Test task approval functionality"""
    print("\n=== Testing Task Approval ===")
    
    # Login as project manager
    session = requests.Session()
    
    # First select role
    response = session.post(f"{BASE_URL}/select_role", data={'role': 'project_manager'})
    print(f"Role selection status: {response.status_code}")
    
    login_data = {
        'emp_id': 'PM001',  # Use emp_id instead of email
        'password': 'manager123'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    print(f"PM login status: {response.status_code}")
    
    if response.status_code in [200, 302]:
        # Try to approve the test task we created
        approval_data = {
            'task_id': 'TEST001',
            'action': 'approve'
        }
        
        response = session.post(f"{BASE_URL}/approve_task", data=approval_data)
        print(f"Task approval status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                return data.get('success', False)
            except:
                print(f"Response text: {response.text}")
                return False
        else:
            print(f"Response text: {response.text[:200]}")
    
    return False

def test_developer_dashboard():
    """Test developer dashboard functionality"""
    print("\n=== Testing Developer Dashboard ===")
    
    # Login as developer
    session = requests.Session()
    
    # First select role
    response = session.post(f"{BASE_URL}/select_role", data={'role': 'developer'})
    print(f"Role selection status: {response.status_code}")
    
    login_data = {
        'emp_id': 'DEV001',  # Use emp_id instead of email
        'password': 'developer123'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    print(f"Developer login status: {response.status_code}")
    
    if response.status_code in [200, 302]:
        # Test developer dashboard
        response = session.get(f"{BASE_URL}/developer_dashboard")
        print(f"Developer dashboard status: {response.status_code}")
        return response.status_code == 200
    
    return False

if __name__ == "__main__":
    print("Starting comprehensive functionality tests...")
    
    results = {
        "admin_employee_creation": test_admin_employee_creation(),
        "pending_review_tasks": test_pending_review_tasks(),
        "task_approval": test_task_approval(),
        "developer_dashboard": test_developer_dashboard()
    }
    
    print("\n=== Test Results Summary ===")
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    overall = all(results.values())
    print(f"\nOverall Status: {'PASS' if overall else 'FAIL'}")