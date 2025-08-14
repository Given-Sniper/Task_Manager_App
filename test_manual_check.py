#!/usr/bin/env python3
"""
Manual check of submission functionality
"""

import requests
import sqlite3

BASE_URL = "http://localhost:5000"

def quick_test():
    """Quick manual test"""
    print("=== Quick Manual Test ===")
    
    # Check if our test task exists
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    cursor.execute('SELECT task_id, status, assigned_to FROM tasks WHERE task_id = ?', ('TASK_SUB_001',))
    task = cursor.fetchone()
    conn.close()
    
    if task:
        print(f"Test task exists: {task[0]}, status: {task[1]}, assigned to: {task[2]}")
    else:
        print("Test task not found")
        return
    
    # Test just the endpoint directly
    session = requests.Session()
    
    # Get the main page to establish session
    try:
        response = session.get(BASE_URL, timeout=5)
        print(f"Main page: {response.status_code}")
    except Exception as e:
        print(f"Cannot access server: {e}")
        return
    
    # Try to get task details without login to see what happens
    try:
        task_response = session.get(f"{BASE_URL}/task_details/TASK_SUB_001", timeout=5, allow_redirects=False)
        print(f"Task details (no login): {task_response.status_code}")
        
        if task_response.status_code == 302:
            print("Redirected to login as expected")
        
    except Exception as e:
        print(f"Error accessing task details: {e}")

if __name__ == "__main__":
    quick_test()