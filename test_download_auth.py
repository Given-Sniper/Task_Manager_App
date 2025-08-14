#!/usr/bin/env python3
"""
Test authorization aspects of developer downloads
"""

import requests
import sqlite3

BASE_URL = "http://localhost:5000"

def login_as_user(role, emp_id, password):
    """Helper to login as specific user"""
    session = requests.Session()
    session.get(BASE_URL)
    session.get(f"{BASE_URL}/select_role/{role}")
    
    login_data = {'emp_id': emp_id, 'password': password}
    response = session.post(f"{BASE_URL}/login", data=login_data)
    
    return session, response.status_code

def test_authorization():
    """Test authorization for different user types"""
    print("=== Testing Download Authorization ===")
    
    # Find a task with spec file assigned to DEV001
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT task_id FROM tasks 
        WHERE spec_zip_path IS NOT NULL AND assigned_to = 'DEV001'
        LIMIT 1
    ''')
    task_result = cursor.fetchone()
    
    if not task_result:
        # Create/update a task for testing
        cursor.execute('''
            SELECT task_id FROM tasks 
            WHERE spec_zip_path IS NOT NULL 
            LIMIT 1
        ''')
        any_task = cursor.fetchone()
        if any_task:
            cursor.execute('UPDATE tasks SET assigned_to = ? WHERE task_id = ?', ('DEV001', any_task[0]))
            conn.commit()
            task_id = any_task[0]
        else:
            print("[INFO] No tasks with spec files found")
            conn.close()
            return True
    else:
        task_id = task_result[0]
    
    conn.close()
    
    print(f"Testing authorization for task: {task_id}")
    
    # Test 1: Assigned developer (DEV001) should have access
    dev1_session, login_status = login_as_user('developer', 'DEV001', 'developer123')
    if login_status in [200, 302]:
        response = dev1_session.get(f"{BASE_URL}/tasks/{task_id}/download-spec")
        if response.status_code == 200:
            print("[PASS] Assigned developer (DEV001) can download")
        else:
            print(f"[FAIL] Assigned developer denied: {response.status_code}")
    
    # Test 2: Different developer (DEV002) should be blocked
    dev2_session, login_status = login_as_user('developer', 'DEV002', 'developer123')
    if login_status in [200, 302]:
        response = dev2_session.get(f"{BASE_URL}/tasks/{task_id}/download-spec", allow_redirects=False)
        if response.status_code in [302, 403]:
            print("[PASS] Non-assigned developer (DEV002) correctly blocked")
        elif response.status_code == 200:
            print("[FAIL] Non-assigned developer was allowed access")
        else:
            print(f"[INFO] Non-assigned developer response: {response.status_code}")
    
    # Test 3: Project Manager should have access
    pm_session, login_status = login_as_user('project_manager', 'PM001', 'manager123')
    if login_status in [200, 302]:
        response = pm_session.get(f"{BASE_URL}/tasks/{task_id}/download-spec")
        if response.status_code == 200:
            print("[PASS] Project Manager can download any task spec")
        else:
            print(f"[FAIL] Project Manager denied: {response.status_code}")
    
    return True

def test_missing_task():
    """Test handling of non-existent tasks"""
    print("\n=== Testing Non-Existent Task Handling ===")
    
    dev_session, login_status = login_as_user('developer', 'DEV001', 'developer123')
    if login_status in [200, 302]:
        response = dev_session.get(f"{BASE_URL}/tasks/NONEXISTENT_TASK/download-spec", allow_redirects=False)
        if response.status_code in [302, 404]:
            print("[PASS] Non-existent task handled gracefully")
        else:
            print(f"[INFO] Non-existent task response: {response.status_code}")
    
    return True

if __name__ == "__main__":
    print("=== AUTHORIZATION TESTS FOR DEVELOPER DOWNLOADS ===")
    
    test_authorization()
    test_missing_task()
    
    print("\n[SUCCESS] Authorization tests completed")