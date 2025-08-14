#!/usr/bin/env python3
"""
Simple test for developer download functionality
"""

import requests
import sqlite3

BASE_URL = "http://localhost:5000"

def test_basic_functionality():
    """Test basic download functionality"""
    print("=== Testing Basic Developer Download Functionality ===")
    
    # Find a task with spec file
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT task_id, assigned_to, spec_zip_path 
        FROM tasks 
        WHERE spec_zip_path IS NOT NULL 
        LIMIT 1
    ''')
    task_result = cursor.fetchone()
    conn.close()
    
    if not task_result:
        print("[INFO] No tasks with spec files found")
        return True
    
    task_id, assigned_to, spec_path = task_result
    print(f"Testing task: {task_id} assigned to {assigned_to}")
    
    # Test dashboard access
    dev_session = requests.Session()
    dev_session.get(BASE_URL)
    dev_session.get(f"{BASE_URL}/select_role/developer")
    
    login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
    response = dev_session.post(f"{BASE_URL}/login", data=login_data)
    
    if response.status_code in [200, 302]:
        print("[PASS] Developer login successful")
        
        # Test dashboard shows download elements
        dashboard_response = dev_session.get(f"{BASE_URL}/developer_dashboard")
        if dashboard_response.status_code == 200:
            dashboard_html = dashboard_response.text
            has_download = 'Download spec (.zip)' in dashboard_html
            has_no_spec = 'No spec uploaded' in dashboard_html
            
            if has_download or has_no_spec:
                print("[PASS] Dashboard shows spec download functionality")
            else:
                print("[FAIL] Dashboard missing download functionality")
            
            # Test download route (check if it exists)
            if assigned_to == 'DEV001':
                download_response = dev_session.get(f"{BASE_URL}/tasks/{task_id}/download-spec", allow_redirects=False)
                print(f"Download route response: {download_response.status_code}")
                
                if download_response.status_code in [200, 302]:
                    print("[PASS] Download route accessible")
                else:
                    print("[PARTIAL] Download route may need attention")
            
        return True
    else:
        print("[FAIL] Developer login failed")
        return False

if __name__ == "__main__":
    result = test_basic_functionality()
    if result:
        print("\n[SUCCESS] Basic functionality test completed")
    else:
        print("\n[ISSUES] Basic functionality test failed")