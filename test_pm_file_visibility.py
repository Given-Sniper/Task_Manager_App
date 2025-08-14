#!/usr/bin/env python3
"""
Test Project Manager's ability to see and download submitted files
"""

import requests
import sqlite3
import tempfile
import zipfile
import os

BASE_URL = "http://localhost:5000"

def check_database_submissions():
    """Check what submissions exist in database"""
    print("=== DATABASE SUBMISSIONS CHECK ===")
    
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Get all submissions
    cursor.execute('''
        SELECT ts.task_id, ts.submit_original_name, ts.notes, ts.submitted_at,
               t.title, t.assigned_to, t.status, t.created_by
        FROM task_submissions ts
        JOIN tasks t ON ts.task_id = t.task_id
        ORDER BY ts.submitted_at DESC
    ''')
    
    submissions = cursor.fetchall()
    print(f"Total submissions in database: {len(submissions)}")
    
    for sub in submissions:
        task_id, file_name, notes, submitted_at, title, assigned_to, status, created_by = sub
        print(f"  Task: {task_id}")
        print(f"    File: {file_name}")
        print(f"    Status: {status}")
        print(f"    Assigned to: {assigned_to}")
        print(f"    Created by: {created_by}")
        print(f"    Submitted: {submitted_at}")
        print()
    
    conn.close()
    return submissions

def test_pm_pending_review_page():
    """Test PM's pending review page to see if submissions are shown"""
    print("=== TESTING PM PENDING REVIEW PAGE ===")
    
    session = requests.Session()
    
    try:
        # Login as PM
        print("Logging in as Project Manager...")
        session.get(BASE_URL, timeout=5)
        session.get(f"{BASE_URL}/select_role/project_manager", timeout=5)
        
        login_data = {'emp_id': 'PM001', 'password': 'manager123'}
        login_response = session.post(f"{BASE_URL}/login", data=login_data, timeout=5)
        
        if login_response.status_code not in [200, 302]:
            print(f"FAIL PM Login failed: {login_response.status_code}")
            return False
        
        print("PASS PM Login successful")
        
        # Get pending review page
        review_response = session.get(f"{BASE_URL}/pending_review_tasks", timeout=10)
        
        if review_response.status_code == 200:
            print("PASS Pending review page loaded")
            
            html = review_response.text
            
            # Check for submission-related elements
            checks = {
                'Submitted tasks section': 'submitted' in html.lower(),
                'Download submission': 'download' in html.lower(),
                'View submission': 'submission' in html.lower(),
                'Task submissions': 'task_submissions' in html or 'task-submissions' in html,
                'Pending approval': 'pending approval' in html.lower() or 'pending_approval' in html
            }
            
            print("\nPending Review Page Content Checks:")
            for check, result in checks.items():
                status = "✅" if result else "❌"
                print(f"  {status} {check}: {result}")
            
            # Look for specific submitted tasks
            print("\nSearching for submitted task indicators...")
            lines = html.split('\n')
            for i, line in enumerate(lines):
                if 'submitted' in line.lower() or 'download' in line.lower():
                    print(f"Line {i+1}: {line.strip()[:120]}")
            
            return True
        else:
            print(f"❌ Pending review page failed: {review_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ PM test failed: {e}")
        return False

def test_pm_dashboard():
    """Test PM dashboard for submitted task visibility"""
    print("\n=== TESTING PM DASHBOARD ===")
    
    session = requests.Session()
    
    try:
        # Login as PM
        session.get(BASE_URL, timeout=3)
        session.get(f"{BASE_URL}/select_role/project_manager", timeout=3)
        
        login_data = {'emp_id': 'PM001', 'password': 'manager123'}
        session.post(f"{BASE_URL}/login", data=login_data, timeout=3)
        
        # Get dashboard
        dashboard_response = session.get(f"{BASE_URL}/project_manager_dashboard", timeout=5)
        
        if dashboard_response.status_code == 200:
            print("✅ PM Dashboard loaded")
            
            html = dashboard_response.text
            
            # Check for submission indicators
            submitted_mentions = html.lower().count('submitted')
            pending_mentions = html.lower().count('pending')
            
            print(f"Dashboard mentions 'submitted': {submitted_mentions} times")
            print(f"Dashboard mentions 'pending': {pending_mentions} times")
            
            # Look for task cards or lists
            if 'task' in html.lower():
                print("✅ Dashboard contains task information")
            else:
                print("❌ Dashboard doesn't seem to show tasks")
            
            return True
        else:
            print(f"❌ PM Dashboard failed: {dashboard_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ PM dashboard test failed: {e}")
        return False

def test_file_download_access():
    """Test if PM can access file download endpoints"""
    print("\n=== TESTING FILE DOWNLOAD ACCESS ===")
    
    # First get submission data from database
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    cursor.execute('SELECT task_id, submit_file_path FROM task_submissions LIMIT 1')
    submission = cursor.fetchone()
    conn.close()
    
    if not submission:
        print("❌ No submissions found to test download")
        return False
    
    task_id, file_path = submission
    print(f"Testing download for task: {task_id}")
    print(f"File path: {file_path}")
    
    session = requests.Session()
    
    try:
        # Login as PM
        session.get(BASE_URL, timeout=3)
        session.get(f"{BASE_URL}/select_role/project_manager", timeout=3)
        
        login_data = {'emp_id': 'PM001', 'password': 'manager123'}
        session.post(f"{BASE_URL}/login", data=login_data, timeout=3)
        
        # Try to download the submission file
        download_url = f"{BASE_URL}/tasks/{task_id}/download-submission"
        download_response = session.get(download_url, timeout=10)
        
        print(f"Download response status: {download_response.status_code}")
        
        if download_response.status_code == 200:
            print("✅ File download successful!")
            print(f"Content-Type: {download_response.headers.get('Content-Type', 'Not specified')}")
            print(f"Content-Length: {len(download_response.content)} bytes")
            return True
        elif download_response.status_code == 404:
            print("❌ File not found - download endpoint might not exist")
            return False
        else:
            print(f"❌ Download failed with status: {download_response.status_code}")
            if download_response.text:
                print(f"Error: {download_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Download test failed: {e}")
        return False

def create_test_submission():
    """Create a test submission to ensure we have data to test with"""
    print("\n=== CREATING TEST SUBMISSION ===")
    
    session = requests.Session()
    
    try:
        # Login as developer
        session.get(BASE_URL, timeout=3)
        session.get(f"{BASE_URL}/select_role/developer", timeout=3)
        
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        session.post(f"{BASE_URL}/login", data=login_data, timeout=3)
        
        # Find an in_progress task
        conn = sqlite3.connect('task_manager.db')
        cursor = conn.cursor()
        cursor.execute('SELECT task_id FROM tasks WHERE assigned_to = ? AND status = ? LIMIT 1', ('DEV001', 'in_progress'))
        in_progress_task = cursor.fetchone()
        conn.close()
        
        if not in_progress_task:
            print("❌ No in_progress tasks found for test submission")
            return False
        
        task_id = in_progress_task[0]
        print(f"Creating test submission for task: {task_id}")
        
        # Create test ZIP file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        with zipfile.ZipFile(temp_file.name, 'w') as zf:
            zf.writestr('pm_test_file.py', 'print("PM visibility test file")')
            zf.writestr('readme.md', '# PM Visibility Test\nThis file tests PM access to submissions')
        
        try:
            with open(temp_file.name, 'rb') as f:
                files = {'submission_file': ('pm_visibility_test.zip', f, 'application/zip')}
                data = {'notes': 'PM visibility test submission - checking if PM can see this'}
                
                upload_response = session.post(
                    f"{BASE_URL}/tasks/{task_id}/submit",
                    files=files,
                    data=data,
                    timeout=10
                )
            
            print(f"Test submission response: {upload_response.status_code}")
            
            if upload_response.status_code in [200, 302]:
                print("✅ Test submission created successfully!")
                return True
            else:
                print(f"❌ Test submission failed: {upload_response.status_code}")
                return False
                
        finally:
            os.unlink(temp_file.name)
            
    except Exception as e:
        print(f"❌ Test submission creation failed: {e}")
        return False

def run_complete_pm_test():
    """Run complete test of PM file visibility"""
    print("TESTING PROJECT MANAGER FILE VISIBILITY")
    print("=" * 50)
    
    # Step 1: Check database state
    submissions = check_database_submissions()
    
    # Step 2: Create test submission if needed
    if len(submissions) == 0:
        print("\n⚠️  No submissions found. Creating test submission...")
        submission_created = create_test_submission()
        if submission_created:
            submissions = check_database_submissions()
    
    # Step 3: Test PM dashboard
    dashboard_works = test_pm_dashboard()
    
    # Step 4: Test PM pending review page
    review_works = test_pm_pending_review_page()
    
    # Step 5: Test file download
    download_works = test_file_download_access()
    
    # Summary
    print("\n" + "=" * 50)
    print("PM VISIBILITY TEST SUMMARY")
    print("=" * 50)
    print(f"Database submissions: {len(submissions)} found")
    print(f"PM Dashboard: {'PASS' if dashboard_works else 'FAIL'}")
    print(f"PM Review page: {'PASS' if review_works else 'FAIL'}")
    print(f"File download: {'PASS' if download_works else 'FAIL'}")
    
    if dashboard_works and review_works and download_works:
        print("\nPM FILE VISIBILITY WORKING!")
    else:
        print("\nSOME PM VISIBILITY ISSUES FOUND")

if __name__ == "__main__":
    run_complete_pm_test()