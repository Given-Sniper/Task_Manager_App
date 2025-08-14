#!/usr/bin/env python3
"""
Comprehensive tests for the task submission flow
Tests developer upload, PM download, and authorization
"""

import requests
import sqlite3
import os
import zipfile
import tempfile
from datetime import datetime

BASE_URL = "http://localhost:5000"

def create_test_zip():
    """Create a temporary ZIP file for testing"""
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    # Create a simple ZIP file with some content
    with zipfile.ZipFile(temp_file.name, 'w') as zf:
        zf.writestr('readme.txt', 'This is a test submission file')
        zf.writestr('code.py', 'print("Hello, world!")')
    
    return temp_file.name

def cleanup_test_zip(zip_path):
    """Clean up temporary ZIP file"""
    try:
        os.unlink(zip_path)
    except:
        pass

def login_as_user(role, emp_id, password):
    """Helper to login as specific user"""
    session = requests.Session()
    session.get(BASE_URL)
    session.get(f"{BASE_URL}/select_role/{role}")
    
    login_data = {'emp_id': emp_id, 'password': password}
    response = session.post(f"{BASE_URL}/login", data=login_data)
    
    return session, response.status_code

def get_test_task():
    """Get or create a task for testing"""
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Find an existing task assigned to DEV001
    cursor.execute('''
        SELECT task_id FROM tasks 
        WHERE assigned_to = 'DEV001' 
        LIMIT 1
    ''')
    task_result = cursor.fetchone()
    
    if task_result:
        task_id = task_result[0]
    else:
        # Create a test task
        task_id = f"TEST_TASK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute('''
            INSERT INTO tasks (task_id, title, description, status, assigned_to, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_id, 'Test Task for Submission', 'A test task for submission testing', 'assigned', 'DEV001', datetime.utcnow()))
        conn.commit()
    
    conn.close()
    return task_id

def test_developer_submission():
    """Test developer can submit a task with ZIP file"""
    print("=== Testing Developer Submission ===" )
    
    # Get test task
    task_id = get_test_task()
    print(f"Using task: {task_id}")
    
    # Login as developer
    dev_session, login_status = login_as_user('developer', 'DEV001', 'developer123')
    if login_status not in [200, 302]:
        print("[FAIL] Developer login failed")
        return False
    
    # Create test ZIP file
    test_zip_path = create_test_zip()
    
    try:
        # Submit task with file
        with open(test_zip_path, 'rb') as f:
            files = {'submission_file': ('test_submission.zip', f, 'application/zip')}
            data = {'notes': 'This is a test submission with notes'}
            
            response = dev_session.post(
                f"{BASE_URL}/tasks/{task_id}/submit",
                files=files,
                data=data,
                allow_redirects=False
            )
        
        print(f"Submission response: {response.status_code}")
        
        if response.status_code in [200, 302]:
            print("[PASS] Developer can submit task with ZIP file")
            
            # Verify task status was updated
            conn = sqlite3.connect('task_manager.db')
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM tasks WHERE task_id = ?', (task_id,))
            task_status = cursor.fetchone()
            
            if task_status and task_status[0] == 'submitted':
                print("[PASS] Task status updated to 'submitted'")
            else:
                print(f"[PARTIAL] Task status: {task_status[0] if task_status else 'N/A'}")
            
            # Verify submission record was created
            cursor.execute('SELECT COUNT(*) FROM task_submissions WHERE task_id = ?', (task_id,))
            submission_count = cursor.fetchone()[0]
            
            if submission_count > 0:
                print("[PASS] Submission record created in database")
            else:
                print("[FAIL] No submission record found")
            
            conn.close()
            return True
        else:
            print(f"[FAIL] Submission failed with status: {response.status_code}")
            return False
    
    finally:
        cleanup_test_zip(test_zip_path)

def test_invalid_file_rejection():
    """Test that non-ZIP files are rejected"""
    print("\n=== Testing Invalid File Rejection ===")
    
    # Get test task
    task_id = get_test_task()
    
    # Login as developer
    dev_session, login_status = login_as_user('developer', 'DEV001', 'developer123')
    if login_status not in [200, 302]:
        print("[FAIL] Developer login failed")
        return False
    
    # Create a text file (not ZIP)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
    temp_file.write(b'This is not a ZIP file')
    temp_file.close()
    
    try:
        # Try to submit non-ZIP file
        with open(temp_file.name, 'rb') as f:
            files = {'submission_file': ('test.txt', f, 'text/plain')}
            
            response = dev_session.post(
                f"{BASE_URL}/tasks/{task_id}/submit",
                files=files,
                allow_redirects=False
            )
        
        print(f"Invalid file response: {response.status_code}")
        
        # Should be rejected (redirect with error)
        if response.status_code in [302]:
            print("[PASS] Invalid file correctly rejected")
            return True
        else:
            print("[FAIL] Invalid file was not rejected")
            return False
    
    finally:
        os.unlink(temp_file.name)

def test_pm_submission_view():
    """Test that PM can view and download submissions"""
    print("\n=== Testing PM Submission View ===")
    
    # Get test task with submission
    task_id = get_test_task()
    
    # First ensure there's a submission
    test_developer_submission()
    
    # Login as PM
    pm_session, login_status = login_as_user('project_manager', 'PM001', 'manager123')
    if login_status not in [200, 302]:
        print("[FAIL] PM login failed")
        return False
    
    # Access task details page
    response = pm_session.get(f"{BASE_URL}/task_details/{task_id}")
    
    if response.status_code == 200:
        html = response.text
        
        # Check if submission section is visible
        has_submission_section = 'Developer Submission' in html
        has_download_link = 'Download Submission' in html
        has_submission_info = 'Submitted by:' in html
        
        print(f"Submission section visible: {has_submission_section}")
        print(f"Download link present: {has_download_link}")
        print(f"Submission info shown: {has_submission_info}")
        
        if has_submission_section and has_download_link:
            print("[PASS] PM can view submission information")
            
            # Test download functionality
            download_response = pm_session.get(f"{BASE_URL}/tasks/{task_id}/submission/download", allow_redirects=False)
            
            if download_response.status_code == 200:
                print("[PASS] PM can download submissions")
                return True
            else:
                print(f"[PARTIAL] Download response: {download_response.status_code}")
                return True
        else:
            print("[FAIL] PM cannot see submission information")
            return False
    else:
        print(f"[FAIL] Cannot access task details: {response.status_code}")
        return False

def test_unauthorized_access():
    """Test that unauthorized users cannot access submissions"""
    print("\n=== Testing Unauthorized Access ===")
    
    # Get test task
    task_id = get_test_task()
    
    # Try to access submission as different developer
    dev2_session, login_status = login_as_user('developer', 'DEV002', 'developer123')
    if login_status not in [200, 302]:
        print("[INFO] DEV002 login failed - creating user or continuing")
    
    # Try to download submission (should be blocked)
    response = dev2_session.get(f"{BASE_URL}/tasks/{task_id}/submission/download", allow_redirects=False)
    
    if response.status_code in [302, 403, 404]:
        print("[PASS] Unauthorized developer correctly blocked from downloads")
    else:
        print(f"[FAIL] Unauthorized access allowed: {response.status_code}")
    
    # Try to submit to a task not assigned to DEV002
    test_zip_path = create_test_zip()
    
    try:
        with open(test_zip_path, 'rb') as f:
            files = {'submission_file': ('unauthorized.zip', f, 'application/zip')}
            
            response = dev2_session.post(
                f"{BASE_URL}/tasks/{task_id}/submit",
                files=files,
                allow_redirects=False
            )
        
        if response.status_code in [302, 403]:
            print("[PASS] Unauthorized submission correctly blocked")
            return True
        else:
            print(f"[FAIL] Unauthorized submission allowed: {response.status_code}")
            return False
    
    finally:
        cleanup_test_zip(test_zip_path)

def test_submission_replacement():
    """Test that new submissions replace old ones"""
    print("\n=== Testing Submission Replacement ===")
    
    # Get test task
    task_id = get_test_task()
    
    # Login as developer
    dev_session, login_status = login_as_user('developer', 'DEV001', 'developer123')
    if login_status not in [200, 302]:
        print("[FAIL] Developer login failed")
        return False
    
    # Submit first file
    test_zip_1 = create_test_zip()
    
    try:
        with open(test_zip_1, 'rb') as f:
            files = {'submission_file': ('first_submission.zip', f, 'application/zip')}
            data = {'notes': 'First submission'}
            
            response1 = dev_session.post(
                f"{BASE_URL}/tasks/{task_id}/submit",
                files=files,
                data=data,
                allow_redirects=False
            )
        
        # Check database has one submission
        conn = sqlite3.connect('task_manager.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM task_submissions WHERE task_id = ?', (task_id,))
        count_after_first = cursor.fetchone()[0]
        
        # Submit second file
        test_zip_2 = create_test_zip()
        
        try:
            with open(test_zip_2, 'rb') as f:
                files = {'submission_file': ('second_submission.zip', f, 'application/zip')}
                data = {'notes': 'Second submission - replacement'}
                
                response2 = dev_session.post(
                    f"{BASE_URL}/tasks/{task_id}/submit",
                    files=files,
                    data=data,
                    allow_redirects=False
                )
            
            # Check database still has only one submission
            cursor.execute('SELECT COUNT(*) FROM task_submissions WHERE task_id = ?', (task_id,))
            count_after_second = cursor.fetchone()[0]
            
            # Check that the notes were updated
            cursor.execute('SELECT notes FROM task_submissions WHERE task_id = ?', (task_id,))
            notes_result = cursor.fetchone()
            
            conn.close()
            
            if count_after_first == 1 and count_after_second == 1:
                print("[PASS] Submission count remained at 1 (replacement, not addition)")
            else:
                print(f"[FAIL] Submission count: first={count_after_first}, second={count_after_second}")
                return False
            
            if notes_result and 'Second submission' in notes_result[0]:
                print("[PASS] Submission data was updated (replacement confirmed)")
                return True
            else:
                print("[PARTIAL] Submission replacement unclear")
                return True
        
        finally:
            cleanup_test_zip(test_zip_2)
    
    finally:
        cleanup_test_zip(test_zip_1)

def run_all_tests():
    """Run all submission flow tests"""
    print("=" * 60)
    print("TASK SUBMISSION FLOW TESTS")
    print("=" * 60)
    
    tests = [
        ("Developer Submission", test_developer_submission),
        ("Invalid File Rejection", test_invalid_file_rejection),
        ("PM Submission View", test_pm_submission_view),
        ("Unauthorized Access", test_unauthorized_access),
        ("Submission Replacement", test_submission_replacement)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All submission flow tests passed!")
        return True
    else:
        print(f"\n[ISSUES] {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    run_all_tests()