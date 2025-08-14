#!/usr/bin/env python3
"""
Test the actual HTML returned by developer dashboard
"""

import requests
import time

BASE_URL = "http://localhost:5000"

def test_dashboard_html():
    print("=== TESTING DASHBOARD HTML OUTPUT ===")
    
    session = requests.Session()
    
    try:
        # Quick login
        print("Logging in...")
        session.get(BASE_URL, timeout=5)
        session.get(f"{BASE_URL}/select_role/developer", timeout=5)
        
        login_data = {'emp_id': 'DEV001', 'password': 'developer123'}
        login_response = session.post(f"{BASE_URL}/login", data=login_data, timeout=5)
        
        if login_response.status_code not in [200, 302]:
            print(f"Login failed: {login_response.status_code}")
            return
        
        print("Login successful, getting dashboard...")
        
        # Get dashboard
        dashboard_response = session.get(f"{BASE_URL}/developer_dashboard", timeout=10)
        
        if dashboard_response.status_code == 200:
            html = dashboard_response.text
            
            print("Dashboard loaded successfully!")
            print(f"HTML length: {len(html)} characters")
            
            # Search for key sections
            sections = {
                'In Progress section': 'In Progress',
                'Submit Your Work': 'Submit Your Work',
                'File input': 'name="submission_file"',
                'ZIP accept': 'accept=".zip"',
                'Submit button': 'Submit Task with File',
                'Upload form': 'enctype="multipart/form-data"'
            }
            
            print("\nSearching for upload elements:")
            for name, search_text in sections.items():
                found = search_text in html
                print(f"  {name}: {'FOUND' if found else 'MISSING'}")
                
                if found:
                    # Find the line number
                    lines = html.split('\n')
                    for i, line in enumerate(lines):
                        if search_text in line:
                            print(f"    -> Line {i+1}: {line.strip()[:80]}...")
                            break
            
            # Check specifically for in-progress tasks section
            print("\nLooking for in-progress tasks section...")
            in_progress_start = html.find('<!-- In Progress Tasks -->')
            if in_progress_start != -1:
                print("Found In Progress section marker")
                
                # Extract the in-progress section
                pending_approval_start = html.find('<!-- Pending Approval Tasks -->', in_progress_start)
                if pending_approval_start != -1:
                    in_progress_section = html[in_progress_start:pending_approval_start]
                else:
                    in_progress_section = html[in_progress_start:in_progress_start+5000]  # Take next 5000 chars
                
                print(f"In Progress section length: {len(in_progress_section)} characters")
                
                # Check if this section contains upload elements
                has_upload_form = 'Submit Your Work' in in_progress_section
                has_file_input = 'submission_file' in in_progress_section
                
                print(f"In Progress section has upload form: {has_upload_form}")
                print(f"In Progress section has file input: {has_file_input}")
                
                # Show a sample of the in-progress section
                print("\nSample of In Progress section:")
                lines = in_progress_section.split('\n')
                for i, line in enumerate(lines[:20]):  # Show first 20 lines
                    if line.strip():
                        print(f"  {i+1:2}: {line.strip()[:100]}")
                
            else:
                print("ERROR: Could not find In Progress section marker!")
                
        else:
            print(f"Dashboard failed: {dashboard_response.status_code}")
            if dashboard_response.text:
                print(f"Error: {dashboard_response.text[:200]}")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_dashboard_html()