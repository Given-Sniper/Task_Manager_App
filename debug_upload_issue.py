#!/usr/bin/env python3
"""
Debug why upload section is not showing for developers
"""

import sqlite3
import requests
import tempfile
import zipfile
import os

BASE_URL = "http://localhost:5000"

def check_database_state():
    """Check current database state"""
    print("=== DATABASE STATE ===")
    
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Check all tasks for DEV001
    cursor.execute('''
        SELECT task_id, title, status, assigned_to 
        FROM tasks 
        WHERE assigned_to = ? 
        ORDER BY status
    ''', ('DEV001',))
    
    tasks = cursor.fetchall()
    print(f"Tasks for DEV001: {len(tasks)}")
    
    status_counts = {}
    for task in tasks:
        status = task[2]
        status_counts[status] = status_counts.get(status, 0) + 1
        print(f"  {task[0]}: {task[1]} - STATUS: {task[2]}")
    
    print(f"\nStatus breakdown: {status_counts}")
    
    # Check specifically for in_progress tasks
    in_progress_count = status_counts.get('in_progress', 0)
    print(f"In-progress tasks: {in_progress_count}")
    
    if in_progress_count == 0:
        print("❌ NO IN-PROGRESS TASKS - Upload form won't show!")
    else:
        print("✅ In-progress tasks exist - Upload form should show")
    
    conn.close()
    return in_progress_count > 0

def test_developer_dashboard_access():
    """Test accessing developer dashboard"""
    print("\n=== TESTING DEVELOPER DASHBOARD ===")
    
    session = requests.Session()
    
    try:
        # Login process
        session.get(BASE_URL, timeout=5)
        session.get(f"{BASE_URL}/select_role/developer", timeout=5)
        
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        login_response = session.post(f"{BASE_URL}/login", data=login_data, timeout=5)
        
        if login_response.status_code not in [200, 302]:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
        
        print("✅ Login successful")
        
        # Get dashboard
        dashboard_response = session.get(f"{BASE_URL}/developer_dashboard", timeout=5)
        
        if dashboard_response.status_code == 200:
            print("✅ Dashboard loaded successfully")
            
            html = dashboard_response.text
            
            # Check for upload-related elements
            checks = {
                'In Progress section': 'In Progress' in html,
                'Submit Your Work': 'Submit Your Work' in html,
                'File input': 'submission_file' in html,
                'Submit Task with File button': 'Submit Task with File' in html,
                'Upload form': 'enctype="multipart/form-data"' in html,
                'ZIP accept': 'accept=".zip"' in html
            }
            
            print("\nDashboard Content Checks:")
            all_good = True
            for check, result in checks.items():
                status = "✅" if result else "❌"
                print(f"  {status} {check}: {result}")
                if not result:
                    all_good = False
            
            if not all_good:
                print("\n❌ Some upload elements are missing!")
                
                # Debug: Show relevant HTML sections
                print("\nDebugging HTML sections:")
                lines = html.split('\n')
                for i, line in enumerate(lines):
                    if 'in progress' in line.lower() or 'submit' in line.lower() or 'upload' in line.lower():
                        print(f"Line {i+1}: {line.strip()[:120]}")
            
            return all_good
        else:
            print(f"❌ Dashboard failed: {dashboard_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_start_task_workflow():
    """Test starting a task to make it in_progress"""
    print("\n=== TESTING START TASK WORKFLOW ===")
    
    session = requests.Session()
    
    try:
        # Login
        session.get(BASE_URL, timeout=3)
        session.get(f"{BASE_URL}/select_role/developer", timeout=3)
        
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        session.post(f"{BASE_URL}/login", data=login_data, timeout=3)
        
        # Try to start an assigned task
        conn = sqlite3.connect('task_manager.db')
        cursor = conn.cursor()
        cursor.execute('SELECT task_id FROM tasks WHERE assigned_to = ? AND status = ? LIMIT 1', ('DEV001', 'assigned'))
        assigned_task = cursor.fetchone()
        conn.close()
        
        if not assigned_task:
            print("❌ No assigned tasks to start")
            return False
        
        task_id = assigned_task[0]
        print(f"Starting task: {task_id}")
        
        # Send start task request
        start_data = {
            'task_id': task_id,
            'status': 'in_progress'
        }
        
        start_response = session.post(
            f"{BASE_URL}/update_task_status",
            json=start_data,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        print(f"Start task response: {start_response.status_code}")
        
        if start_response.status_code == 200:
            print("✅ Task started successfully")
            
            # Verify status change
            conn = sqlite3.connect('task_manager.db')
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM tasks WHERE task_id = ?', (task_id,))
            new_status = cursor.fetchone()
            conn.close()
            
            if new_status and new_status[0] == 'in_progress':
                print(f"✅ Task status updated to: {new_status[0]}")
                return True
            else:
                print(f"❌ Status not updated correctly: {new_status[0] if new_status else 'None'}")
                return False
        else:
            print(f"❌ Start task failed: {start_response.status_code}")
            if start_response.text:
                print(f"Response: {start_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Start task test failed: {e}")
        return False

def create_test_zip():
    """Create a test ZIP file"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    with zipfile.ZipFile(temp_file.name, 'w') as zf:
        zf.writestr('completed_work.py', 'print("Developer work completed!")')
        zf.writestr('documentation.md', '# Project Documentation\nCompleted by developer')
    return temp_file.name

def test_file_upload():
    """Test actual file upload"""
    print("\n=== TESTING FILE UPLOAD ===")
    
    session = requests.Session()
    
    try:
        # Login
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
            print("❌ No in_progress tasks for upload test")
            return False
        
        task_id = in_progress_task[0]
        print(f"Testing upload for task: {task_id}")
        
        # Create test file
        test_zip = create_test_zip()
        
        try:
            with open(test_zip, 'rb') as f:
                files = {'submission_file': ('debug_test_work.zip', f, 'application/zip')}
                data = {'notes': 'Debug test upload - checking if upload works'}
                
                upload_response = session.post(
                    f"{BASE_URL}/tasks/{task_id}/submit",
                    files=files,
                    data=data,
                    timeout=10
                )
            
            print(f"Upload response: {upload_response.status_code}")
            
            if upload_response.status_code in [200, 302]:
                print("✅ File upload successful!")
                
                # Check if submission was recorded
                conn = sqlite3.connect('task_manager.db')
                cursor = conn.cursor()
                cursor.execute('SELECT submit_original_name, notes FROM task_submissions WHERE task_id = ?', (task_id,))
                submission = cursor.fetchone()
                conn.close()
                
                if submission:
                    print(f"✅ Submission recorded: {submission[0]}")
                    print(f"   Notes: {submission[1]}")
                    return True
                else:
                    print("❌ Submission not found in database")
                    return False
            else:
                print(f"❌ Upload failed: {upload_response.status_code}")
                return False
                
        finally:
            os.unlink(test_zip)
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False

def run_full_debug():
    """Run complete debugging sequence"""
    print("🔍 DEBUGGING UPLOAD ISSUE")
    print("=" * 50)
    
    # Step 1: Check database
    has_in_progress = check_database_state()
    
    # Step 2: Test dashboard access
    dashboard_works = test_developer_dashboard_access()
    
    # Step 3: If no in_progress tasks, try to start one
    if not has_in_progress:
        print("\n⚠️  No in_progress tasks found. Trying to start one...")
        start_works = test_start_task_workflow()
        if start_works:
            # Re-test dashboard after starting task
            dashboard_works = test_developer_dashboard_access()
    
    # Step 4: Test actual upload
    upload_works = test_file_upload()
    
    # Summary
    print("\n" + "=" * 50)
    print("🔍 DEBUG SUMMARY")
    print("=" * 50)
    print(f"Database state: {'✅' if has_in_progress else '❌'}")
    print(f"Dashboard rendering: {'✅' if dashboard_works else '❌'}")
    print(f"File upload: {'✅' if upload_works else '❌'}")
    
    if has_in_progress and dashboard_works and upload_works:
        print("\n🎉 ALL SYSTEMS WORKING!")
    else:
        print("\n⚠️  ISSUES FOUND - Check output above")

if __name__ == "__main__":
    run_full_debug()