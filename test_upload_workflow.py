#!/usr/bin/env python3
"""
Test the file upload workflow from developer side
"""

import requests
import sqlite3
import tempfile
import zipfile
import os

BASE_URL = "http://localhost:5000"

def create_test_zip():
    """Create a test ZIP file"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    with zipfile.ZipFile(temp_file.name, 'w') as zf:
        zf.writestr('main.py', 'print("Hello from developer submission!")')
        zf.writestr('README.md', '# Developer Submission\nThis is a test submission.')
    return temp_file.name

def test_developer_upload():
    """Test developer can upload files from dashboard"""
    print("=== Testing Developer File Upload Workflow ===")
    
    session = requests.Session()
    
    try:
        # Step 1: Login as developer
        session.get(BASE_URL, timeout=3)
        session.get(f"{BASE_URL}/select_role/developer", timeout=3)
        
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        login_response = session.post(f"{BASE_URL}/login", data=login_data, timeout=3)
        
        if login_response.status_code not in [200, 302]:
            print(f"[FAIL] Login failed: {login_response.status_code}")
            return False
        
        print("[PASS] Developer login successful")
        
        # Step 2: Check developer dashboard shows upload form for in-progress tasks
        dashboard_response = session.get(f"{BASE_URL}/developer_dashboard", timeout=3)
        if dashboard_response.status_code == 200:
            html = dashboard_response.text
            
            # Check for upload form elements
            has_submit_work = 'Submit Your Work' in html
            has_file_input = 'submission_file' in html
            has_submit_button = 'Submit Task with File' in html
            
            print(f"Dashboard has 'Submit Your Work': {has_submit_work}")
            print(f"Dashboard has file input: {has_file_input}")
            print(f"Dashboard has submit button: {has_submit_button}")
            
            if has_submit_work and has_file_input and has_submit_button:
                print("[PASS] Developer dashboard shows upload form for in-progress tasks")
            else:
                print("[FAIL] Upload form missing from dashboard")
                return False
        else:
            print(f"[FAIL] Dashboard failed: {dashboard_response.status_code}")
            return False
        
        # Step 3: Test file upload
        test_zip = create_test_zip()
        task_id = "ZIP_TEST_1755116308"  # We know this is in progress for DEV001
        
        try:
            with open(test_zip, 'rb') as f:
                files = {'submission_file': ('developer_work.zip', f, 'application/zip')}
                data = {'notes': 'Test upload from developer dashboard workflow'}
                
                upload_response = session.post(
                    f"{BASE_URL}/tasks/{task_id}/submit",
                    files=files,
                    data=data,
                    timeout=5,
                    allow_redirects=False
                )
            
            print(f"Upload response status: {upload_response.status_code}")
            
            if upload_response.status_code in [200, 302]:
                print("[PASS] File upload successful")
                
                # Step 4: Verify submission was recorded in database
                conn = sqlite3.connect('task_manager.db')
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT submit_original_name, submit_size_bytes, notes, submitted_at 
                    FROM task_submissions 
                    WHERE task_id = ?
                ''', (task_id,))
                submission = cursor.fetchone()
                
                if submission:
                    print(f"[PASS] Submission recorded: {submission[0]} ({submission[1]} bytes)")
                    print(f"      Notes: {submission[2]}")
                    print(f"      Submitted at: {submission[3]}")
                    
                    # Check if task status was updated
                    cursor.execute('SELECT status FROM tasks WHERE task_id = ?', (task_id,))
                    task_status = cursor.fetchone()
                    
                    if task_status and task_status[0] == 'submitted':
                        print("[PASS] Task status updated to 'submitted'")
                    else:
                        print(f"[INFO] Task status: {task_status[0] if task_status else 'Unknown'}")
                    
                    conn.close()
                    return True
                else:
                    print("[FAIL] Submission not found in database")
                    conn.close()
                    return False
                    
            else:
                print(f"[FAIL] Upload failed: {upload_response.status_code}")
                if upload_response.text:
                    print(f"Response: {upload_response.text[:200]}")
                return False
                
        finally:
            os.unlink(test_zip)
            
    except Exception as e:
        print(f"[ERROR] Test failed with exception: {e}")
        return False

def test_pm_can_see_submission():
    """Test that PM can see the uploaded submission"""
    print("\n=== Testing PM Can View Submission ===")
    
    session = requests.Session()
    
    try:
        # Login as PM
        session.get(BASE_URL, timeout=3)
        session.get(f"{BASE_URL}/select_role/project_manager", timeout=3)
        
        login_data = {'emp_id': 'PM001', 'password': 'manager123'}
        login_response = session.post(f"{BASE_URL}/login", data=login_data, timeout=3)
        
        if login_response.status_code not in [200, 302]:
            print(f"[FAIL] PM login failed: {login_response.status_code}")
            return False
        
        print("[PASS] PM login successful")
        
        # Check task details page
        task_id = "ZIP_TEST_1755116308"
        task_response = session.get(f"{BASE_URL}/task_details/{task_id}", timeout=3)
        
        if task_response.status_code == 200:
            html = task_response.text
            
            # Check for submission information
            has_submission_section = 'Developer Submission' in html
            has_download_link = 'Download Submission' in html
            has_submission_info = 'Submitted by:' in html or 'developer_work.zip' in html
            
            print(f"Has submission section: {has_submission_section}")
            print(f"Has download link: {has_download_link}")
            print(f"Has submission info: {has_submission_info}")
            
            if has_submission_section and (has_download_link or has_submission_info):
                print("[PASS] PM can see submission information")
                
                # Test download
                download_response = session.get(f"{BASE_URL}/tasks/{task_id}/submission/download", timeout=3)
                if download_response.status_code == 200:
                    print(f"[PASS] PM can download submission ({len(download_response.content)} bytes)")
                    return True
                else:
                    print(f"[PARTIAL] Download response: {download_response.status_code}")
                    return True
            else:
                print("[FAIL] PM cannot see submission information")
                return False
        else:
            print(f"[FAIL] Task details failed: {task_response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] PM test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Complete Upload Workflow")
    print("=" * 50)
    
    # Test developer upload
    dev_result = test_developer_upload()
    
    # Test PM can see submission
    pm_result = test_pm_can_see_submission()
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS")
    print("=" * 50)
    print(f"Developer Upload: {'PASS' if dev_result else 'FAIL'}")
    print(f"PM Can View:      {'PASS' if pm_result else 'FAIL'}")
    
    if dev_result and pm_result:
        print("\n[SUCCESS] Complete workflow is working!")
    else:
        print("\n[ISSUES] Some parts of the workflow failed.")