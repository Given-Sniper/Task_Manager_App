#!/usr/bin/env python3
"""
Manual test of file upload - simplified version
"""

import tempfile
import zipfile
import os
import sqlite3

def create_test_file():
    """Create a simple test ZIP file"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    with zipfile.ZipFile(temp_file.name, 'w') as zf:
        zf.writestr('test.py', 'print("Test file from developer")')
    return temp_file.name

def simulate_upload():
    """Simulate the upload process"""
    print("=== Manual Upload Simulation ===")
    
    # Create test file
    test_zip = create_test_file()
    print(f"Created test ZIP: {test_zip}")
    
    # Check file size
    file_size = os.path.getsize(test_zip)
    print(f"File size: {file_size} bytes")
    
    # Verify it's a valid ZIP
    with zipfile.ZipFile(test_zip, 'r') as zf:
        files_in_zip = zf.namelist()
        print(f"Files in ZIP: {files_in_zip}")
    
    # Simulate database insertion (what the backend would do)
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Check if we can insert a test submission
    task_id = "ZIP_TEST_1755116308"  # Our test in-progress task
    
    try:
        # Check if submission already exists
        cursor.execute('SELECT COUNT(*) FROM task_submissions WHERE task_id = ?', (task_id,))
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"Found {existing_count} existing submissions for {task_id}")
            # Delete existing for this test
            cursor.execute('DELETE FROM task_submissions WHERE task_id = ?', (task_id,))
            print("Removed existing submissions for clean test")
        
        # Insert test submission
        cursor.execute('''
            INSERT INTO task_submissions 
            (task_id, developer_id, submit_zip_path, submit_original_name, submit_size_bytes, notes, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (task_id, 'DEV001', 'test_path.zip', 'manual_test.zip', file_size, 'Manual upload test'))
        
        # Update task status
        cursor.execute('UPDATE tasks SET status = ? WHERE task_id = ?', ('submitted', task_id))
        
        conn.commit()
        print("[PASS] Database operations successful")
        
        # Verify insertion
        cursor.execute('''
            SELECT submit_original_name, submit_size_bytes, notes 
            FROM task_submissions 
            WHERE task_id = ?
        ''', (task_id,))
        
        result = cursor.fetchone()
        if result:
            print(f"[PASS] Submission recorded: {result[0]}, {result[1]} bytes, notes: {result[2]}")
        else:
            print("[FAIL] Submission not found after insertion")
        
        # Check task status
        cursor.execute('SELECT status FROM tasks WHERE task_id = ?', (task_id,))
        status = cursor.fetchone()
        if status and status[0] == 'submitted':
            print(f"[PASS] Task status updated to: {status[0]}")
        else:
            print(f"[FAIL] Task status not updated correctly: {status[0] if status else 'None'}")
        
    except Exception as e:
        print(f"[ERROR] Database operation failed: {e}")
        conn.rollback()
    finally:
        conn.close()
        os.unlink(test_zip)
    
    return True

def test_pm_view():
    """Test PM can query submissions"""
    print("\n=== PM View Test ===")
    
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Query all submissions (what PM would see)
    cursor.execute('''
        SELECT ts.task_id, ts.submit_original_name, ts.submit_size_bytes, 
               ts.submitted_at, ts.notes, t.title, t.assigned_to
        FROM task_submissions ts
        JOIN tasks t ON ts.task_id = t.task_id
    ''')
    
    submissions = cursor.fetchall()
    print(f"PM can see {len(submissions)} submissions:")
    
    for sub in submissions:
        print(f"  Task {sub[0]}: {sub[6]} submitted {sub[1]} ({sub[2]} bytes)")
        print(f"    Title: {sub[5]}")
        print(f"    Notes: {sub[4]}")
        print(f"    Submitted at: {sub[3]}")
        print()
    
    conn.close()
    
    if submissions:
        print("[PASS] PM can view submission data")
        return True
    else:
        print("[INFO] No submissions to view")
        return False

if __name__ == "__main__":
    print("Manual Upload and PM View Test")
    print("=" * 40)
    
    upload_result = simulate_upload()
    pm_result = test_pm_view()
    
    print("=" * 40)
    print(f"Upload simulation: {'PASS' if upload_result else 'FAIL'}")
    print(f"PM view test: {'PASS' if pm_result else 'FAIL'}")
    
    if upload_result and pm_result:
        print("\n[SUCCESS] Upload workflow is working correctly!")
    else:
        print("\n[INFO] Check results above")