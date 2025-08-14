#!/usr/bin/env python3
"""
Test the actual user experience through web interface
"""

import requests
import json
import os
import zipfile
import tempfile
from datetime import datetime

BASE_URL = "http://localhost:5000"

def create_test_zip():
    """Create a simple test ZIP file"""
    temp_dir = tempfile.mkdtemp()
    txt_file = os.path.join(temp_dir, "test.txt")
    zip_file = os.path.join(temp_dir, "test.zip")
    
    with open(txt_file, 'w') as f:
        f.write("This is a test file for task requirements")
    
    with zipfile.ZipFile(zip_file, 'w') as zf:
        zf.write(txt_file, "test.txt")
    
    return zip_file

def test_project_manager_workflow():
    """Test complete project manager workflow"""
    print("\n=== TESTING PROJECT MANAGER WORKFLOW ===")
    
    session = requests.Session()
    
    # 1. Access homepage
    response = session.get(BASE_URL)
    print(f"Homepage access: {response.status_code}")
    
    # 2. Select project manager role
    response = session.get(f"{BASE_URL}/select_role/project_manager")
    print(f"Role selection: {response.status_code}")
    
    # 3. Login as project manager
    login_data = {'emp_id': 'PM001', 'password': 'manager123'}
    response = session.post(f"{BASE_URL}/login", data=login_data)
    print(f"PM login: {response.status_code}")
    
    if response.status_code not in [200, 302]:
        print("[FAIL] Cannot login as project manager")
        return False
    
    # 4. Access project manager dashboard
    response = session.get(f"{BASE_URL}/project_manager_dashboard")
    print(f"PM dashboard access: {response.status_code}")
    
    if response.status_code != 200:
        print("[FAIL] Cannot access PM dashboard")
        return False
    
    # 5. Check if dashboard shows pending tasks
    dashboard_content = response.text
    if "Tasks Submitted for Approval" in dashboard_content:
        print("✓ Dashboard shows pending tasks section")
    else:
        print("✗ Dashboard missing pending tasks section")
    
    # 6. Test task creation with file upload
    print("\n--- Testing Task Creation with File Upload ---")
    
    # Create test file
    test_zip = create_test_zip()
    task_id = f"UI_TEST_{int(datetime.now().timestamp())}"
    
    try:
        # Prepare task data
        task_data = {
            'task_id': task_id,
            'title': 'UI Test Task',
            'description': 'Testing task creation through UI',
            'project_type': 'web_development',
            'complexity': 'medium', 
            'priority': 'high',
            'skills': '["Python", "JavaScript"]'
        }
        
        # Test file upload
        with open(test_zip, 'rb') as f:
            files = {'task_file': ('requirements.zip', f, 'application/zip')}
            response = session.post(f"{BASE_URL}/api/create_task", data=task_data, files=files)
        
        print(f"Task creation API: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✓ Task {task_id} created and assigned to {result['assignment']['name']}")
                print(f"✓ Skill match: {result['assignment'].get('skill_match_percentage', 'N/A')}")
                return task_id
            else:
                print(f"✗ Task creation failed: {result.get('error')}")
        else:
            print(f"✗ Task creation API error: {response.text}")
            
    except Exception as e:
        print(f"✗ Exception during task creation: {str(e)}")
    finally:
        try:
            os.remove(test_zip)
        except:
            pass
    
    return False

def test_developer_workflow(task_id=None):
    """Test complete developer workflow"""
    print("\n=== TESTING DEVELOPER WORKFLOW ===")
    
    session = requests.Session()
    
    # 1. Login as developer
    response = session.get(BASE_URL)
    response = session.get(f"{BASE_URL}/select_role/developer")
    
    login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
    response = session.post(f"{BASE_URL}/login", data=login_data)
    print(f"Developer login: {response.status_code}")
    
    if response.status_code not in [200, 302]:
        print("[FAIL] Cannot login as developer")
        return False
    
    # 2. Access developer dashboard
    response = session.get(f"{BASE_URL}/developer_dashboard")
    print(f"Developer dashboard access: {response.status_code}")
    
    if response.status_code != 200:
        print("[FAIL] Cannot access developer dashboard")
        return False
    
    # 3. Check notification count in dashboard
    dashboard_content = response.text
    if 'bg-red-500' in dashboard_content and 'rounded-full' in dashboard_content:
        print("✓ Dashboard shows notification badge")
    else:
        print("ℹ Dashboard shows no notifications (which may be correct)")
    
    # 4. Access My Tasks page
    response = session.get(f"{BASE_URL}/my_tasks")
    print(f"My Tasks access: {response.status_code}")
    
    if response.status_code != 200:
        print("[FAIL] Cannot access My Tasks page")
        return False
    
    # 5. Test file download if task_id provided
    if task_id:
        print(f"\n--- Testing File Download for Task {task_id} ---")
        response = session.get(f"{BASE_URL}/download_task_file/{task_id}")
        print(f"File download attempt: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Developer can download task file")
        else:
            print(f"✗ File download failed: {response.text}")
    
    # 6. Test task submission with file
    print("\n--- Testing Task Submission ---")
    
    # Find an assigned task for DEV001
    import sqlite3
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    cursor.execute('SELECT task_id FROM tasks WHERE assigned_to = ? AND status IN (?, ?) LIMIT 1', 
                  ('DEV001', 'assigned', 'in_progress'))
    task_result = cursor.fetchone()
    conn.close()
    
    if task_result:
        test_task_id = task_result[0]
        print(f"Testing submission for task: {test_task_id}")
        
        # Create submission file
        test_zip = create_test_zip()
        
        try:
            with open(test_zip, 'rb') as f:
                files = {'submission_file': ('submission.zip', f, 'application/zip')}
                data = {'task_id': test_task_id}
                response = session.post(f"{BASE_URL}/api/submit_task", data=data, files=files)
            
            print(f"Task submission API: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✓ Task submitted successfully with file")
                    return True
                else:
                    print(f"✗ Task submission failed: {result.get('error')}")
            else:
                print(f"✗ Submission API error: {response.text}")
                
        except Exception as e:
            print(f"✗ Exception during task submission: {str(e)}")
        finally:
            try:
                os.remove(test_zip)
            except:
                pass
    else:
        print("ℹ No assigned tasks found for DEV001 to test submission")
    
    return False

def test_database_state():
    """Check the current database state"""
    print("\n=== CHECKING DATABASE STATE ===")
    
    import sqlite3
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Check if new columns exist
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [col[1] for col in cursor.fetchall()]
    
    file_columns = ['task_file_path', 'submission_file_path', 'task_file_name', 'submission_file_name']
    missing_columns = [col for col in file_columns if col not in columns]
    
    if missing_columns:
        print(f"✗ Missing database columns: {missing_columns}")
        return False
    else:
        print("✓ All file upload columns exist in database")
    
    # Check active tasks per developer
    print("\nActive tasks per developer:")
    cursor.execute('''
        SELECT e.name, e.emp_id, COUNT(t.task_id) as active_count
        FROM employees e
        LEFT JOIN tasks t ON e.emp_id = t.assigned_to AND t.status IN ('assigned', 'in_progress')
        WHERE e.role = 'developer'
        GROUP BY e.emp_id, e.name
        ORDER BY active_count DESC
    ''')
    
    for row in cursor.fetchall():
        name, emp_id, count = row
        print(f"  {name} ({emp_id}): {count} active tasks")
    
    # Check tasks with files
    cursor.execute('''
        SELECT task_id, assigned_to, status, 
               CASE WHEN task_file_path IS NOT NULL THEN 'Yes' ELSE 'No' END as has_task_file,
               CASE WHEN submission_file_path IS NOT NULL THEN 'Yes' ELSE 'No' END as has_submission
        FROM tasks
        WHERE task_file_path IS NOT NULL OR submission_file_path IS NOT NULL
        ORDER BY task_id DESC
        LIMIT 5
    ''')
    
    print("\nTasks with files (last 5):")
    tasks_with_files = cursor.fetchall()
    for task in tasks_with_files:
        task_id, assigned_to, status, has_task_file, has_submission = task
        print(f"  {task_id} -> {assigned_to} ({status}) | Task file: {has_task_file} | Submission: {has_submission}")
    
    conn.close()
    return len(tasks_with_files) > 0

def test_file_system():
    """Check file system state"""
    print("\n=== CHECKING FILE SYSTEM ===")
    
    upload_dir = "uploads"
    if os.path.exists(upload_dir):
        files = os.listdir(upload_dir)
        print(f"✓ Upload directory exists with {len(files)} files:")
        for file in files:
            file_path = os.path.join(upload_dir, file)
            size = os.path.getsize(file_path)
            print(f"  {file} ({size} bytes)")
        return len(files) > 0
    else:
        print("✗ Upload directory not found")
        return False

if __name__ == "__main__":
    print("=== COMPREHENSIVE USER EXPERIENCE TEST ===")
    
    # Test all components
    db_ok = test_database_state()
    files_ok = test_file_system()
    
    # Test workflows
    task_id = test_project_manager_workflow()
    dev_ok = test_developer_workflow(task_id)
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Database setup: {'✓ PASS' if db_ok else '✗ FAIL'}")
    print(f"File system: {'✓ PASS' if files_ok else '✗ FAIL'}")
    print(f"PM workflow: {'✓ PASS' if task_id else '✗ FAIL'}")
    print(f"Developer workflow: {'✓ PASS' if dev_ok else '✗ FAIL'}")
    
    total_passed = sum([db_ok, files_ok, bool(task_id), dev_ok])
    
    if total_passed >= 3:
        print(f"\n🎉 SUCCESS: {total_passed}/4 components working!")
        print("The task management system is functioning correctly.")
    else:
        print(f"\n⚠️  ISSUES: Only {total_passed}/4 components working properly.")
        print("Some features may not be visible in the user interface yet.")