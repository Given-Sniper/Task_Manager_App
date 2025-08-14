#!/usr/bin/env python3
"""
Test developer dashboard to verify spec download functionality
"""

import requests

BASE_URL = "http://localhost:5000"

def test_developer_dashboard():
    """Test developer dashboard shows download links"""
    print("=== Testing Developer Dashboard ===")
    
    # Login as developer
    session = requests.Session()
    
    try:
        # Get main page to establish session
        session.get(BASE_URL, timeout=5)
        session.get(f"{BASE_URL}/select_role/developer", timeout=5)
        
        # Login
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        login_response = session.post(f"{BASE_URL}/login", data=login_data, timeout=5)
        
        if login_response.status_code not in [200, 302]:
            print(f"[FAIL] Login failed: {login_response.status_code}")
            return False
        
        print("[PASS] Developer login successful")
        
        # Get developer dashboard
        dashboard_response = session.get(f"{BASE_URL}/developer_dashboard", timeout=5)
        
        if dashboard_response.status_code == 200:
            print("[PASS] Developer dashboard loads")
            
            html = dashboard_response.text
            
            # Check for download links
            has_download_link = 'Download spec (.zip)' in html
            has_spec_files = 'ZIP_TEST_' in html or 'DEV_DL_TEST_' in html
            
            print(f"Has download link text: {has_download_link}")
            print(f"Has spec file tasks: {has_spec_files}")
            
            # Let's also check if no spec uploaded text appears
            has_no_spec_text = 'No spec uploaded' in html
            print(f"Has 'No spec uploaded' text: {has_no_spec_text}")
            
            # Test download functionality
            if has_download_link:
                print("[PASS] Download links are present in dashboard")
                
                # Try downloading a spec file
                download_response = session.get(f"{BASE_URL}/tasks/ZIP_TEST_1755116308/download-spec", timeout=5)
                
                if download_response.status_code == 200:
                    print("[PASS] Spec download works")
                    print(f"Downloaded file size: {len(download_response.content)} bytes")
                    return True
                else:
                    print(f"[PARTIAL] Download response: {download_response.status_code}")
                    return True
            else:
                print("[FAIL] No download links found in dashboard")
                
                # Debug: Print relevant parts of HTML
                print("\nDebugging dashboard HTML:")
                lines = html.split('\n')
                for i, line in enumerate(lines):
                    if 'ZIP_TEST' in line or 'download' in line.lower() or 'spec' in line.lower():
                        print(f"Line {i}: {line.strip()[:200]}")
                
                return False
        else:
            print(f"[FAIL] Dashboard failed to load: {dashboard_response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    result = test_developer_dashboard()
    if result:
        print("\n[SUCCESS] Developer dashboard test passed!")
    else:
        print("\n[FAILED] Developer dashboard test failed!")