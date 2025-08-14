#!/usr/bin/env python3
"""
Simple test for submission functionality
"""

import requests
import sqlite3
import os
import zipfile
import tempfile

BASE_URL = "http://localhost:5000"

def create_test_zip():
    """Create a test ZIP file"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    with zipfile.ZipFile(temp_file.name, 'w') as zf:
        zf.writestr('test.py', 'print("Hello from submission!")')
    
    return temp_file.name

def test_basic_submission():
    """Test basic submission functionality"""
    print("=== Testing Basic Submission ===")
    
    # Create test task in database
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Check if we have any assigned tasks for DEV001
    cursor.execute('SELECT task_id FROM tasks WHERE assigned_to = ? AND status = ? LIMIT 1', ('DEV001', 'assigned'))
    task_result = cursor.fetchone()
    
    if not task_result:
        print("No assigned tasks found for DEV001 - using TASK_SUB_001")
        task_id = "TASK_SUB_001"
    else:
        task_id = task_result[0]
        print(f"Using existing assigned task: {task_id}")
    
    conn.close()
    
    # Login as developer
    session = requests.Session()
    session.get(BASE_URL)
    session.get(f"{BASE_URL}/select_role/developer")
    
    login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
    response = session.post(f"{BASE_URL}/login", data=login_data)
    
    if response.status_code not in [200, 302]:
        print(f"Login failed: {response.status_code}")
        return False
    
    print("[PASS] Developer login successful")
    
    # Test task details page loads
    details_response = session.get(f"{BASE_URL}/task_details/{task_id}")
    if details_response.status_code == 200:
        print("[PASS] Task details page loads")
        
        # Check if upload form is present
        html = details_response.text
        if 'Submit Your Work' in html and 'submission_file' in html:
            print("[PASS] Upload form is present")
        else:
            print("[FAIL] Upload form missing")
            return False
    else:
        print(f"[FAIL] Task details page failed: {details_response.status_code}")
        return False
    
    # Test file submission
    test_zip_path = create_test_zip()
    
    try:
        with open(test_zip_path, 'rb') as f:
            files = {'submission_file': ('test_submission.zip', f, 'application/zip')}
            data = {'notes': 'Test submission notes'}
            
            submit_response = session.post(
                f"{BASE_URL}/tasks/{task_id}/submit",
                files=files,
                data=data,
                allow_redirects=False
            )
        
        if submit_response.status_code in [200, 302]:
            print("[PASS] File submission successful")
            
            # Check database for submission record
            conn = sqlite3.connect('task_manager.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM task_submissions WHERE task_id = ?', (task_id,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("[PASS] Submission record created in database")
                
                # Check task status
                cursor.execute('SELECT status FROM tasks WHERE task_id = ?', (task_id,))
                status_result = cursor.fetchone()
                
                if status_result and status_result[0] == 'submitted':
                    print("[PASS] Task status updated to 'submitted'")
                else:
                    print(f"[FAIL] Task status not updated correctly: {status_result[0] if status_result else 'None'}")
            else:
                print("[FAIL] No submission record found")
                
            conn.close()
            return True
        else:
            print(f"[FAIL] File submission failed: {submit_response.status_code}")
            print(f"Response text: {submit_response.text[:200]}")
            return False
    
    finally:
        os.unlink(test_zip_path)

if __name__ == "__main__":
    try:
        result = test_basic_submission()
        if result:
            print("\n[SUCCESS] Basic submission test PASSED!")
        else:
            print("\n[FAILED] Basic submission test FAILED!")
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {str(e)}")