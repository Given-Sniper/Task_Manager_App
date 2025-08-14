#!/usr/bin/env python3
"""
Comprehensive test for ZIP upload during Project Manager task creation.
Tests all requirements: validation, file storage, security, and download functionality.
"""

import requests
import os
import zipfile
import tempfile
import sqlite3
from datetime import datetime
import json

BASE_URL = "http://localhost:5000"

def create_test_zip_file(filename="test_spec.zip", content="Test specification content"):
    """Create a temporary ZIP file for testing"""
    temp_dir = tempfile.mkdtemp()
    txt_file = os.path.join(temp_dir, "specification.txt")
    zip_file = os.path.join(temp_dir, filename)
    
    # Create text file with content
    with open(txt_file, 'w') as f:
        f.write(content)
    
    # Create ZIP file
    with zipfile.ZipFile(zip_file, 'w') as zf:
        zf.write(txt_file, "specification.txt")
    
    return zip_file

def create_invalid_file(filename="invalid.txt"):
    """Create a non-ZIP file for testing rejection"""
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, filename)
    
    with open(file_path, 'w') as f:
        f.write("This is not a ZIP file")
    
    return file_path

def login_as_pm():
    """Login as Project Manager and return session"""
    session = requests.Session()
    
    # Access homepage and select role
    session.get(BASE_URL)
    session.get(f"{BASE_URL}/select_role/project_manager")
    
    # Login
    login_data = {'emp_id': 'PM001', 'password': 'manager123'}
    response = session.post(f"{BASE_URL}/login", data=login_data)
    
    return session, response.status_code

def login_as_developer():
    """Login as Developer and return session"""
    session = requests.Session()
    
    # Access homepage and select role
    session.get(BASE_URL)
    session.get(f"{BASE_URL}/select_role/developer")
    
    # Login
    login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
    response = session.post(f"{BASE_URL}/login", data=login_data)
    
    return session, response.status_code

def test_zip_upload_success():
    """Test successful ZIP file upload"""
    print("\n=== Testing Valid ZIP Upload ===")
    
    session, login_status = login_as_pm()
    if login_status not in [200, 302]:
        print(f"[FAIL] Could not login as PM: {login_status}")
        return False
    
    # Create test ZIP file
    test_zip = create_test_zip_file("requirements.zip", "Task specifications and requirements")
    task_id = f"ZIP_TEST_{int(datetime.now().timestamp())}"
    
    try:
        # Prepare task data
        task_data = {
            'task_id': task_id,
            'title': 'ZIP Upload Test Task',
            'description': 'Testing ZIP file upload functionality',
            'project_type': 'web_development',
            'complexity': 'medium',
            'priority': 'high'
        }
        
        # Upload with ZIP file
        with open(test_zip, 'rb') as f:
            files = {'spec_file': ('requirements.zip', f, 'application/zip')}
            response = session.post(f"{BASE_URL}/api/create_task", data=task_data, files=files)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"[PASS] Task created with ZIP file")
                print(f"  - Task ID: {task_id}")
                print(f"  - Assigned to: {result['assignment']['name']}")
                print(f"  - Spec file: {result['task']['spec_file_name']}")
                print(f"  - File size: {result['task']['spec_file_size']} bytes")
                
                # Verify in database
                return verify_task_in_database(task_id)
            else:
                print(f"[FAIL] Task creation failed: {result.get('error')}")
                return False
        else:
            print(f"[FAIL] HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}")
        return False
    finally:
        try:
            os.remove(test_zip)
        except:
            pass

def test_non_zip_rejection():
    """Test rejection of non-ZIP files"""
    print("\n=== Testing Non-ZIP File Rejection ===")
    
    session, login_status = login_as_pm()
    if login_status not in [200, 302]:
        print(f"[FAIL] Could not login as PM: {login_status}")
        return False
    
    # Create non-ZIP file
    invalid_file = create_invalid_file("document.txt")
    task_id = f"INVALID_TEST_{int(datetime.now().timestamp())}"
    
    try:
        task_data = {
            'task_id': task_id,
            'title': 'Invalid File Test',
            'description': 'Testing invalid file rejection',
            'project_type': 'web_development',
            'complexity': 'medium',
            'priority': 'medium'
        }
        
        # Try to upload non-ZIP file
        with open(invalid_file, 'rb') as f:
            files = {'spec_file': ('document.txt', f, 'text/plain')}
            response = session.post(f"{BASE_URL}/api/create_task", data=task_data, files=files)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 400:
            result = response.json()
            error_msg = result.get('error', '')
            if 'zip' in error_msg.lower():
                print(f"[PASS] Non-ZIP file correctly rejected: {error_msg}")
                return True
            else:
                print(f"[FAIL] Wrong error message: {error_msg}")
                return False
        else:
            print(f"[FAIL] Expected 400 error but got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}")
        return False
    finally:
        try:
            os.remove(invalid_file)
        except:
            pass

def test_missing_file_rejection():
    """Test rejection when no file is provided"""
    print("\n=== Testing Missing File Rejection ===")
    
    session, login_status = login_as_pm()
    if login_status not in [200, 302]:
        print(f"[FAIL] Could not login as PM: {login_status}")
        return False
    
    try:
        task_data = {
            'task_id': f"NO_FILE_TEST_{int(datetime.now().timestamp())}",
            'title': 'No File Test',
            'description': 'Testing missing file rejection',
            'project_type': 'web_development',
            'complexity': 'medium',
            'priority': 'medium'
        }
        
        # Submit as multipart form data but without file
        files = {'spec_file': ('', '')}  # Empty filename to trigger validation
        response = session.post(f"{BASE_URL}/api/create_task", data=task_data, files=files)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 400:
            result = response.json()
            error_msg = result.get('error', '')
            if 'required' in error_msg.lower():
                print(f"[PASS] Missing file correctly rejected: {error_msg}")
                return True
            else:
                print(f"[FAIL] Wrong error message: {error_msg}")
                return False
        else:
            print(f"[FAIL] Expected 400 error but got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}")
        return False

def test_file_storage_structure():
    """Test that files are stored in correct directory structure"""
    print("\n=== Testing File Storage Structure ===")
    
    # Check if upload directories exist and have proper structure
    base_upload_dir = "instance/uploads"
    tasks_dir = os.path.join(base_upload_dir, "tasks")
    
    if not os.path.exists(base_upload_dir):
        print(f"[FAIL] Base upload directory missing: {base_upload_dir}")
        return False
    
    print(f"[PASS] Base upload directory exists: {base_upload_dir}")
    
    if os.path.exists(tasks_dir):
        print(f"[PASS] Tasks directory exists: {tasks_dir}")
        
        # List task directories
        task_dirs = [d for d in os.listdir(tasks_dir) if os.path.isdir(os.path.join(tasks_dir, d))]
        print(f"[INFO] Found {len(task_dirs)} task directories")
        
        for task_dir in task_dirs[:3]:  # Show first 3
            task_path = os.path.join(tasks_dir, task_dir)
            files = os.listdir(task_path)
            print(f"  - {task_dir}: {len(files)} files")
            
        return len(task_dirs) > 0
    else:
        print(f"[INFO] No tasks directory yet (will be created on first upload)")
        return True

def test_secure_download():
    """Test secure download functionality"""
    print("\n=== Testing Secure Download ===")
    
    # First find a task with spec file
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT task_id, spec_zip_path, spec_original_name, assigned_to 
        FROM tasks 
        WHERE spec_zip_path IS NOT NULL 
        LIMIT 1
    ''')
    task_result = cursor.fetchone()
    conn.close()
    
    if not task_result:
        print("[INFO] No tasks with spec files found for download test")
        return True
    
    task_id, spec_path, original_name, assigned_to = task_result
    print(f"Testing download for task: {task_id}")
    
    # Test as Project Manager (should work)
    pm_session, pm_login = login_as_pm()
    if pm_login in [200, 302]:
        response = pm_session.get(f"{BASE_URL}/download_spec_file/{task_id}")
        if response.status_code == 200:
            print("[PASS] PM can download spec file")
            pm_success = True
        else:
            print(f"[FAIL] PM download failed: {response.status_code}")
            pm_success = False
    else:
        print("[FAIL] Could not login as PM")
        pm_success = False
    
    # Test as assigned Developer (should work)
    dev_session, dev_login = login_as_developer()
    if dev_login in [200, 302]:
        response = dev_session.get(f"{BASE_URL}/download_spec_file/{task_id}")
        if response.status_code == 200 and assigned_to == 'DEV001':
            print("[PASS] Assigned developer can download spec file")
            dev_success = True
        elif response.status_code == 403 and assigned_to != 'DEV001':
            print("[PASS] Non-assigned developer correctly denied access")
            dev_success = True
        else:
            print(f"[FAIL] Developer download result: {response.status_code}")
            dev_success = False
    else:
        print("[FAIL] Could not login as developer")
        dev_success = False
    
    return pm_success and dev_success

def verify_task_in_database(task_id):
    """Verify task was properly saved with spec file metadata"""
    try:
        conn = sqlite3.connect('task_manager.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT task_id, spec_zip_path, spec_original_name, spec_size_bytes, spec_uploaded_at
            FROM tasks WHERE task_id = ?
        ''', (task_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            tid, path, name, size, uploaded = result
            print(f"[PASS] Task in database with spec metadata:")
            print(f"  - Path: {path}")
            print(f"  - Original name: {name}")
            print(f"  - Size: {size} bytes")
            print(f"  - Uploaded: {uploaded}")
            
            # Check if file exists
            if path and os.path.exists(path):
                print(f"[PASS] Spec file exists on filesystem")
                return True
            else:
                print(f"[FAIL] Spec file missing from filesystem: {path}")
                return False
        else:
            print(f"[FAIL] Task not found in database")
            return False
            
    except Exception as e:
        print(f"[FAIL] Database verification error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== ZIP UPLOAD FUNCTIONALITY TEST ===")
    
    # Run all tests
    tests = {
        "Valid ZIP Upload": test_zip_upload_success(),
        "Non-ZIP Rejection": test_non_zip_rejection(),
        "Missing File Rejection": test_missing_file_rejection(),
        "File Storage Structure": test_file_storage_structure(),
        "Secure Download": test_secure_download()
    }
    
    print(f"\n=== TEST RESULTS ===")
    passed = 0
    total = len(tests)
    
    for test_name, result in tests.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All ZIP upload functionality working correctly!")
        print("Features verified:")
        print("- ZIP file validation and upload")
        print("- Non-ZIP file rejection")
        print("- Required file validation")
        print("- Organized file storage (instance/uploads/tasks/<task_id>/)")
        print("- Secure authenticated downloads")
        print("- Database metadata storage")
    else:
        print(f"\n[ISSUES] {total - passed} tests failed")
        print("Some ZIP upload features may need attention")