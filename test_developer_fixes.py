#!/usr/bin/env python3
"""
Test developer dashboard fixes
"""

import requests
import sqlite3
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_developer_login_with_new_password():
    """Test that developers can login with developer123"""
    print("\n=== Testing Developer Login with New Password ===")
    
    session = requests.Session()
    
    try:
        # Access index
        response = session.get(BASE_URL)
        print(f"Index access: {response.status_code}")
        
        # Select developer role
        response = session.get(f"{BASE_URL}/select_role/developer")
        print(f"Role selection: {response.status_code}")
        
        # Try logging in with DEV001 and new password
        login_data = {
            'emp_id': 'DEV001',
            'password': 'developer123'
        }
        response = session.post(f"{BASE_URL}/login", data=login_data)
        print(f"Login with developer123: {response.status_code}")
        
        if response.status_code in [200, 302]:
            # Try accessing developer dashboard
            response = session.get(f"{BASE_URL}/developer_dashboard")
            print(f"Developer dashboard access: {response.status_code}")
            
            if response.status_code == 200:
                # Check if the response contains expected elements (not perfect but good enough for test)
                if "Notifications" in response.text and "Experience" in response.text:
                    print("[PASS] Developer dashboard loads correctly")
                    return True
                else:
                    print("[FAIL] Dashboard content issue")
            else:
                print(f"[FAIL] Dashboard access failed: {response.status_code}")
        else:
            print("[FAIL] Login failed")
            
    except Exception as e:
        print(f"[FAIL] Exception during login test: {str(e)}")
    
    return False

def test_notification_count():
    """Test that notification count is dynamic"""
    print("\n=== Testing Notification Count ===")
    
    # Check notification count in database for DEV001
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Count assigned and submitted tasks for DEV001
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE assigned_to = ? AND status IN (?, ?)', 
                  ('DEV001', 'assigned', 'submitted'))
    expected_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"Expected notification count for DEV001: {expected_count}")
    
    # Login and check if dashboard shows correct count
    session = requests.Session()
    
    try:
        # Quick login process
        session.get(BASE_URL)
        session.get(f"{BASE_URL}/select_role/developer")
        
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        session.post(f"{BASE_URL}/login", data=login_data)
        
        # Get dashboard
        response = session.get(f"{BASE_URL}/developer_dashboard")
        
        if response.status_code == 200:
            # Look for notification badge in HTML
            if expected_count > 0:
                if f'>{expected_count}<' in response.text:
                    print(f"[PASS] Notification count {expected_count} found in dashboard")
                    return True
                else:
                    print(f"[FAIL] Expected count {expected_count} not found in HTML")
                    return False
            else:
                # If count is 0, badge should not appear
                if 'bg-red-500' not in response.text or 'rounded-full' not in response.text:
                    print("[PASS] No notification badge when count is 0")
                    return True
                else:
                    print("[FAIL] Badge appears when count should be 0")
                    return False
        else:
            print(f"[FAIL] Dashboard access failed: {response.status_code}")
            
    except Exception as e:
        print(f"[FAIL] Exception during notification test: {str(e)}")
    
    return False

def test_experience_display():
    """Test that experience shows just years without 'with company'"""
    print("\n=== Testing Experience Display ===")
    
    session = requests.Session()
    
    try:
        # Login as developer
        session.get(BASE_URL)
        session.get(f"{BASE_URL}/select_role/developer")
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        session.post(f"{BASE_URL}/login", data=login_data)
        
        # Get dashboard
        response = session.get(f"{BASE_URL}/developer_dashboard")
        
        if response.status_code == 200:
            # Check that "with company" is NOT in the response
            if "with company" not in response.text:
                print("[PASS] 'with company' text removed from experience section")
                return True
            else:
                print("[FAIL] 'with company' text still appears in experience section")
                return False
        else:
            print(f"[FAIL] Dashboard access failed: {response.status_code}")
            
    except Exception as e:
        print(f"[FAIL] Exception during experience test: {str(e)}")
    
    return False

def test_new_developer_creation():
    """Test creating new developer with developer123 password"""
    print("\n=== Testing New Developer Creation ===")
    
    # Create test data
    test_email = f"newdev{int(datetime.now().timestamp())}@example.com"
    
    try:
        # Test through admin interface
        session = requests.Session()
        session.get(BASE_URL)
        session.get(f"{BASE_URL}/select_role/admin")
        
        login_data = {'emp_id': 'ADMIN001', 'password': 'admin123'}
        response = session.post(f"{BASE_URL}/login", data=login_data)
        
        if response.status_code in [200, 302]:
            # Create new developer
            employee_data = {
                'name': 'Test New Developer',
                'email': test_email,
                'role': 'developer',
                'experience': '1',
                'password': 'ignored',  # Should be overridden
                'skills': 'Testing'
            }
            
            response = session.post(f"{BASE_URL}/admin/create_employee", data=employee_data)
            print(f"Employee creation: {response.status_code}")
            
            if response.status_code in [200, 302]:
                # Check database for new employee
                conn = sqlite3.connect('task_manager.db')
                cursor = conn.cursor()
                cursor.execute('SELECT emp_id FROM employees WHERE email = ?', (test_email,))
                new_emp = cursor.fetchone()
                conn.close()
                
                if new_emp:
                    emp_id = new_emp[0]
                    print(f"[INFO] New developer created: {emp_id}")
                    
                    # Try to login with new developer using developer123
                    new_session = requests.Session()
                    new_session.get(BASE_URL)
                    new_session.get(f"{BASE_URL}/select_role/developer")
                    
                    login_data = {'emp_id': emp_id, 'password': 'developer123'}
                    response = new_session.post(f"{BASE_URL}/login", data=login_data)
                    
                    if response.status_code in [200, 302]:
                        print("[PASS] New developer can login with developer123")
                        return True
                    else:
                        print("[FAIL] New developer cannot login with developer123")
                        return False
                else:
                    print("[FAIL] New developer not found in database")
                    return False
            else:
                print(f"[FAIL] Employee creation failed: {response.status_code}")
        else:
            print(f"[FAIL] Admin login failed: {response.status_code}")
            
    except Exception as e:
        print(f"[FAIL] Exception during new developer test: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("=== TESTING DEVELOPER DASHBOARD FIXES ===")
    
    results = {
        "developer_login_new_password": test_developer_login_with_new_password(),
        "notification_count_dynamic": test_notification_count(), 
        "experience_display_clean": test_experience_display(),
        "new_developer_creation": test_new_developer_creation()
    }
    
    print("\n=== RESULTS SUMMARY ===")
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All developer dashboard fixes are working correctly!")
    else:
        print(f"\n[PARTIAL] {passed} out of {total} fixes are working")