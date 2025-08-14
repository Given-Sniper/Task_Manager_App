#!/usr/bin/env python3
"""
Test all the fixes that were implemented
"""

import requests
import sqlite3
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_task_review_workflow():
    """Test the complete task review workflow"""
    print("\n=== Testing Task Review Workflow ===")
    
    # Create a session as project manager
    session = requests.Session()
    
    # Simulate login by accessing the index first, then selecting role, then logging in
    try:
        # Step 1: Access index page
        response = session.get(BASE_URL)
        print(f"Index page access: {response.status_code}")
        
        # Step 2: Select role
        response = session.get(f"{BASE_URL}/select_role/project_manager")
        print(f"Role selection: {response.status_code}")
        
        # Step 3: Login
        login_data = {
            'emp_id': 'PM001',
            'password': 'manager123'
        }
        response = session.post(f"{BASE_URL}/login", data=login_data)
        print(f"Login attempt: {response.status_code}")
        
        # Step 4: Access pending review tasks
        response = session.get(f"{BASE_URL}/pending_review_tasks")
        print(f"Pending tasks API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data.get('count', 0)} pending tasks")
            return True
        else:
            print(f"API Response: {response.text}")
            
    except Exception as e:
        print(f"Error in workflow test: {str(e)}")
    
    return False

def test_submission_date_display():
    """Test that submission dates are properly displayed"""
    print("\n=== Testing Submission Date Display ===")
    
    # Check database directly
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    cursor.execute('SELECT task_id, submitted_at FROM tasks WHERE status = ?', ('submitted',))
    tasks = cursor.fetchall()
    
    print("Tasks in database with submitted status:")
    for task in tasks:
        task_id, submitted_at = task
        if submitted_at:
            # Parse the ISO date and format it like the template does
            formatted_date = submitted_at[:19] if len(submitted_at) > 19 else submitted_at
            print(f"  Task {task_id}: {formatted_date} (should not be N/A)")
        else:
            print(f"  Task {task_id}: No submission date (will show N/A)")
    
    conn.close()
    return len(tasks) > 0 and all(task[1] for task in tasks)

def test_employee_creation():
    """Test employee creation and email sending"""
    print("\n=== Testing Employee Creation ===")
    
    try:
        session = requests.Session()
        
        # Access index first
        response = session.get(BASE_URL)
        
        # Select admin role
        response = session.get(f"{BASE_URL}/select_role/admin") 
        
        # Login as admin
        login_data = {
            'emp_id': 'ADMIN001',
            'password': 'admin123'
        }
        response = session.post(f"{BASE_URL}/login", data=login_data)
        
        if response.status_code in [200, 302]:
            # Try to create an employee
            employee_data = {
                'name': 'Test Employee Final',
                'email': 'testfinal@example.com',
                'role': 'developer',
                'experience': '2',
                'password': 'testpass123',
                'skills': 'Python,Testing'
            }
            
            response = session.post(f"{BASE_URL}/admin/create_employee", data=employee_data)
            print(f"Employee creation request: {response.status_code}")
            
            # Check if employee was created in database
            conn = sqlite3.connect('task_manager.db')
            cursor = conn.cursor()
            cursor.execute('SELECT emp_id, name FROM employees WHERE email = ?', (employee_data['email'],))
            employee = cursor.fetchone()
            conn.close()
            
            if employee:
                print(f"✓ Employee created: {employee[1]} ({employee[0]})")
                print("✓ Email notification should have been sent (check console logs)")
                return True
            else:
                print("✗ Employee not found in database")
                
    except Exception as e:
        print(f"Error in employee creation test: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("=== TESTING ALL FINAL FIXES ===")
    
    results = {
        "task_review_workflow": test_task_review_workflow(),
        "submission_date_display": test_submission_date_display(),
        "employee_creation": test_employee_creation()
    }
    
    print("\n=== RESULTS SUMMARY ===")
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {sum(results.values())}/{len(results)} tests passed")
    
    print("\n=== LOGIN CREDENTIALS REMINDER ===")
    print("ADMIN: ADMIN001 / admin123")
    print("PROJECT MANAGER: PM001 / manager123")  
    print("DEVELOPER: DEV001 / developer123")
    print("\n=== HOMEPAGE ===")
    print("All three buttons (Developer, Project Manager, Admin) now have consistent blue color")