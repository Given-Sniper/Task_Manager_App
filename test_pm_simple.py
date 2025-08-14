#!/usr/bin/env python3
"""
Simple test for PM file visibility
"""

import requests
import sqlite3

BASE_URL = "http://localhost:5000"

def check_submissions():
    """Check database submissions"""
    print("=== DATABASE SUBMISSIONS ===")
    
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ts.task_id, ts.submit_original_name, t.status, t.assigned_to
        FROM task_submissions ts
        JOIN tasks t ON ts.task_id = t.task_id
    ''')
    
    submissions = cursor.fetchall()
    print(f"Found {len(submissions)} submissions:")
    
    for sub in submissions:
        task_id, file_name, status, assigned_to = sub
        print(f"  {task_id}: {file_name} (status: {status}, assigned: {assigned_to})")
    
    conn.close()
    return submissions

def test_pm_access():
    """Test PM access to submissions"""
    print("\n=== TESTING PM ACCESS ===")
    
    session = requests.Session()
    
    try:
        # Login as PM
        session.get(BASE_URL)
        session.get(f"{BASE_URL}/select_role/project_manager")
        
        login_data = {'emp_id': 'PM001', 'password': 'manager123'}
        login_response = session.post(f"{BASE_URL}/login", data=login_data)
        
        if login_response.status_code not in [200, 302]:
            print(f"PM Login failed: {login_response.status_code}")
            return False
        
        print("PM Login successful")
        
        # Test pending review page
        review_response = session.get(f"{BASE_URL}/pending_review_tasks")
        
        if review_response.status_code == 200:
            print("Pending review page loaded")
            
            html = review_response.text
            
            # Check for submission indicators
            has_submissions = 'submission' in html.lower()
            has_download = 'download' in html.lower()
            has_submitted = 'submitted' in html.lower()
            
            print(f"Page has 'submission': {has_submissions}")
            print(f"Page has 'download': {has_download}")
            print(f"Page has 'submitted': {has_submitted}")
            
            return True
        else:
            print(f"Pending review page failed: {review_response.status_code}")
            return False
            
    except Exception as e:
        print(f"PM test failed: {e}")
        return False

def test_file_download():
    """Test file download"""
    print("\n=== TESTING FILE DOWNLOAD ===")
    
    # Get a submission to test
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    cursor.execute('SELECT task_id FROM task_submissions LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print("No submissions to test download")
        return False
    
    task_id = result[0]
    print(f"Testing download for task: {task_id}")
    
    session = requests.Session()
    
    try:
        # Login as PM
        session.get(BASE_URL)
        session.get(f"{BASE_URL}/select_role/project_manager")
        
        login_data = {'emp_id': 'PM001', 'password': 'manager123'}
        session.post(f"{BASE_URL}/login", data=login_data)
        
        # Try download
        download_url = f"{BASE_URL}/tasks/{task_id}/submission/download"
        download_response = session.get(download_url)
        
        print(f"Download response: {download_response.status_code}")
        
        if download_response.status_code == 200:
            print("File download successful!")
            return True
        else:
            print(f"Download failed: {download_response.status_code}")
            return False
            
    except Exception as e:
        print(f"Download test failed: {e}")
        return False

def main():
    print("TESTING PM FILE VISIBILITY")
    print("=" * 40)
    
    # Check database
    submissions = check_submissions()
    
    # Test PM access
    pm_access = test_pm_access()
    
    # Test download
    download_works = test_file_download()
    
    # Summary
    print("\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)
    print(f"Submissions found: {len(submissions)}")
    print(f"PM access works: {pm_access}")
    print(f"Download works: {download_works}")
    
    if pm_access and download_works:
        print("\nPM FILE VISIBILITY IS WORKING!")
    else:
        print("\nISSUES FOUND WITH PM FILE VISIBILITY")

if __name__ == "__main__":
    main()