#!/usr/bin/env python3
"""
Test that developer dashboard shows download links properly
"""

import requests

BASE_URL = "http://localhost:5000"

def test_dashboard_ui():
    """Test dashboard UI elements"""
    print("=== Testing Developer Dashboard UI ===")
    
    # Login as developer
    session = requests.Session()
    session.get(BASE_URL)
    session.get(f"{BASE_URL}/select_role/developer")
    
    login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
    response = session.post(f"{BASE_URL}/login", data=login_data)
    
    if response.status_code not in [200, 302]:
        print("[FAIL] Could not login")
        return False
    
    # Get dashboard
    dashboard_response = session.get(f"{BASE_URL}/developer_dashboard")
    
    if dashboard_response.status_code == 200:
        html = dashboard_response.text
        
        # Check for spec download elements
        has_download_link = 'Download spec (.zip)' in html
        has_no_spec_text = 'No spec uploaded' in html
        has_download_icon = 'fa-download' in html
        has_archive_icon = 'fa-file-archive' in html
        has_spec_download_section = 'Specification Download' in html
        
        print(f"Download link present: {has_download_link}")
        print(f"'No spec uploaded' text: {has_no_spec_text}")
        print(f"Download icon present: {has_download_icon}")
        print(f"Archive icon present: {has_archive_icon}")
        print(f"Spec download section: {has_spec_download_section}")
        
        if has_download_link or has_no_spec_text:
            print("\n[PASS] Dashboard properly shows spec download functionality")
            return True
        else:
            print("\n[FAIL] Dashboard missing spec download elements")
            # Show a snippet of what's actually in the dashboard
            print("Dashboard snippet (looking for task elements):")
            lines = html.split('\n')
            for i, line in enumerate(lines):
                if 'task-card' in line.lower() or 'download' in line.lower():
                    print(f"Line {i}: {line.strip()[:100]}...")
            return False
    else:
        print(f"[FAIL] Could not access dashboard: {dashboard_response.status_code}")
        return False

if __name__ == "__main__":
    result = test_dashboard_ui()
    if result:
        print("\n[SUCCESS] Dashboard UI test passed")
    else:
        print("\n[ISSUES] Dashboard UI test failed")