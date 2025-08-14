#!/usr/bin/env python3
"""
Test task details page functionality
"""

import requests
import sqlite3

BASE_URL = "http://localhost:5000"

def test_task_details():
    """Test task details page"""
    print("=== Testing Task Details Page ===")
    
    # First, check what tasks DEV001 has
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT task_id, title, status, assigned_to 
        FROM tasks 
        WHERE assigned_to = ? 
        ORDER BY task_id
    ''', ('DEV001',))
    
    tasks = cursor.fetchall()
    print("Tasks for DEV001:")
    for task in tasks:
        print(f"  {task[0]}: {task[1]} (status: {task[2]})")
    
    conn.close()
    
    if not tasks:
        print("No tasks found for DEV001")
        return False
    
    # Test with the first task
    test_task_id = tasks[0][0]
    print(f"\nTesting with task: {test_task_id}")
    
    # Login as developer
    session = requests.Session()
    
    try:
        print("Attempting login...")
        session.get(BASE_URL, timeout=3)
        session.get(f"{BASE_URL}/select_role/developer", timeout=3)
        
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        login_response = session.post(f"{BASE_URL}/login", data=login_data, timeout=3)
        
        if login_response.status_code not in [200, 302]:
            print(f"[FAIL] Login failed: {login_response.status_code}")
            return False
        
        print("[PASS] Login successful")
        
        # Access task details
        print(f"Accessing task details for {test_task_id}...")
        task_response = session.get(f"{BASE_URL}/task_details/{test_task_id}", timeout=3)
        
        if task_response.status_code == 200:
            print("[PASS] Task details page loads")
            
            html = task_response.text
            
            # Check for submission form
            has_submit_form = 'Submit Your Work' in html
            has_file_input = 'submission_file' in html
            has_upload_button = 'Upload Submission' in html or 'Replace Submission' in html
            
            print(f"Has 'Submit Your Work' section: {has_submit_form}")
            print(f"Has file input: {has_file_input}")
            print(f"Has upload button: {has_upload_button}")
            
            # Check task status in the HTML
            task_status_in_html = None
            if 'Assigned' in html:
                task_status_in_html = 'assigned'
            elif 'In Progress' in html:
                task_status_in_html = 'in_progress'
            elif 'Completed' in html:
                task_status_in_html = 'completed'
            elif 'Submitted' in html:
                task_status_in_html = 'submitted'
            
            print(f"Task status visible in HTML: {task_status_in_html}")
            
            if has_submit_form and has_file_input:
                print("[PASS] Submission form is present and complete")
                return True
            else:
                print("[FAIL] Submission form is missing or incomplete")
                
                # Debug output
                print("\nDebugging HTML content:")
                lines = html.split('\n')
                for i, line in enumerate(lines):
                    if 'submit' in line.lower() or 'upload' in line.lower() or 'assigned' in line.lower():
                        print(f"Line {i}: {line.strip()[:150]}")
                
                return False
        else:
            print(f"[FAIL] Task details page failed: {task_response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    result = test_task_details()
    if result:
        print("\n[SUCCESS] Task details test passed!")
    else:
        print("\n[FAILED] Task details test failed!")