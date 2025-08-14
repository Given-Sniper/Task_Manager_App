#!/usr/bin/env python3
"""
End-to-end test to verify all fixes are working:
1. Developer can see and download spec files from dashboard
2. Developer can submit work on assigned/in-progress tasks
3. PM dashboard shows correct active tasks count
"""

import requests
import sqlite3
import tempfile
import zipfile
import os

BASE_URL = "http://localhost:5000"

def create_test_zip():
    """Create a test ZIP file for submission"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    with zipfile.ZipFile(temp_file.name, 'w') as zf:
        zf.writestr('test.py', 'print("Test submission file")')
    return temp_file.name

def test_developer_workflow():
    """Test developer can see specs and submit work"""
    print("=== Testing Developer Workflow ===")
    
    session = requests.Session()
    
    try:
        # Login as developer
        response = session.get(BASE_URL, timeout=2)
        session.get(f"{BASE_URL}/select_role/developer", timeout=2)
        
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        login_response = session.post(f"{BASE_URL}/login", data=login_data, timeout=2)
        
        if login_response.status_code not in [200, 302]:
            print(f"[FAIL] Developer login failed: {login_response.status_code}")
            return False
        
        print("[PASS] Developer login successful")
        
        # Test 1: Check developer dashboard shows download links
        dashboard_response = session.get(f"{BASE_URL}/developer_dashboard", timeout=2)
        if dashboard_response.status_code == 200:
            html = dashboard_response.text
            has_download_links = 'Download spec (.zip)' in html
            has_spec_tasks = any(task_id in html for task_id in ['ZIP_TEST_1755116308', 'DEV_DL_TEST_1755117826'])
            
            if has_download_links and has_spec_tasks:
                print("[PASS] Developer dashboard shows spec download links")
            else:
                print(f"[FAIL] Dashboard missing download links: has_links={has_download_links}, has_tasks={has_spec_tasks}")
                return False
        else:
            print(f"[FAIL] Dashboard failed: {dashboard_response.status_code}")
            return False
        
        # Test 2: Check task details page shows submission form for submittable tasks
        task_response = session.get(f"{BASE_URL}/task_details/TASK_SUB_001", timeout=2)
        if task_response.status_code == 200:
            task_html = task_response.text
            has_submit_form = 'Submit Your Work' in task_html
            has_file_input = 'submission_file' in task_html
            
            if has_submit_form and has_file_input:
                print("[PASS] Task details shows submission form for submittable task")
            else:
                print(f"[FAIL] Submission form missing: submit_form={has_submit_form}, file_input={has_file_input}")
                return False
        else:
            print(f"[FAIL] Task details failed: {task_response.status_code}")
            return False
        
        # Test 3: Try to submit a file
        test_zip = create_test_zip()
        try:
            with open(test_zip, 'rb') as f:
                files = {'submission_file': ('test_submission.zip', f, 'application/zip')}
                data = {'notes': 'End-to-end test submission'}
                
                submit_response = session.post(
                    f"{BASE_URL}/tasks/TASK_SUB_001/submit",
                    files=files,
                    data=data,
                    timeout=3,
                    allow_redirects=False
                )
            
            if submit_response.status_code in [200, 302]:
                print("[PASS] File submission successful")
                
                # Verify submission was recorded
                conn = sqlite3.connect('task_manager.db')
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM task_submissions WHERE task_id = ?', ('TASK_SUB_001',))
                count = cursor.fetchone()[0]
                conn.close()
                
                if count > 0:
                    print("[PASS] Submission recorded in database")
                else:
                    print("[FAIL] Submission not recorded")
                    return False
            else:
                print(f"[FAIL] File submission failed: {submit_response.status_code}")
                return False
                
        finally:
            os.unlink(test_zip)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Developer workflow test failed: {e}")
        return False

def test_pm_workflow():
    """Test PM dashboard shows correct active tasks count"""
    print("\n=== Testing PM Workflow ===")
    
    session = requests.Session()
    
    try:
        # Login as PM
        session.get(BASE_URL, timeout=2)
        session.get(f"{BASE_URL}/select_role/project_manager", timeout=2)
        
        login_data = {'emp_id': 'PM001', 'password': 'manager123'}
        login_response = session.post(f"{BASE_URL}/login", data=login_data, timeout=2)
        
        if login_response.status_code not in [200, 302]:
            print(f"[FAIL] PM login failed: {login_response.status_code}")
            return False
        
        print("[PASS] PM login successful")
        
        # Check PM dashboard
        dashboard_response = session.get(f"{BASE_URL}/project_manager_dashboard", timeout=3)
        if dashboard_response.status_code == 200:
            html = dashboard_response.text
            
            # Look for active tasks count in the HTML
            # The count should be 12 based on our database state
            expected_count = "12"
            if expected_count in html and 'Active Tasks' in html:
                print(f"[PASS] PM dashboard shows active tasks count ({expected_count})")
                return True
            else:
                print("[FAIL] PM dashboard doesn't show correct active tasks count")
                # Debug: show relevant parts
                lines = html.split('\n')
                for i, line in enumerate(lines):
                    if 'active' in line.lower() or 'task' in line.lower():
                        if any(char.isdigit() for char in line):
                            print(f"  Line {i}: {line.strip()[:100]}")
                return False
        else:
            print(f"[FAIL] PM dashboard failed: {dashboard_response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] PM workflow test failed: {e}")
        return False

def test_completed_task_submission():
    """Test that submission form doesn't appear for completed tasks"""
    print("\n=== Testing Completed Task Submission ===")
    
    session = requests.Session()
    
    try:
        # Login as developer
        session.get(BASE_URL, timeout=2)
        session.get(f"{BASE_URL}/select_role/developer", timeout=2)
        
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        session.post(f"{BASE_URL}/login", data=login_data, timeout=2)
        
        # Check a completed task (TASK001 is completed)
        task_response = session.get(f"{BASE_URL}/task_details/TASK001", timeout=2)
        if task_response.status_code == 200:
            task_html = task_response.text
            has_submit_form = 'Submit Your Work' in task_html
            has_info_message = 'Submission not available' in task_html
            
            if not has_submit_form and has_info_message:
                print("[PASS] Completed task correctly hides submission form and shows info message")
                return True
            else:
                print(f"[FAIL] Completed task behavior wrong: submit_form={has_submit_form}, info_msg={has_info_message}")
                return False
        else:
            print(f"[FAIL] Completed task details failed: {task_response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Completed task test failed: {e}")
        return False

def run_end_to_end_tests():
    """Run all end-to-end tests"""
    print("=" * 60)
    print("END-TO-END TESTS FOR ALL FIXES")
    print("=" * 60)
    
    results = []
    
    # Test developer workflow
    results.append(("Developer Workflow", test_developer_workflow()))
    
    # Test PM workflow
    results.append(("PM Workflow", test_pm_workflow()))
    
    # Test completed task behavior
    results.append(("Completed Task Behavior", test_completed_task_submission()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All end-to-end tests PASSED! All fixes are working correctly.")
        return True
    else:
        print(f"\n[ISSUES] {total - passed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    run_end_to_end_tests()