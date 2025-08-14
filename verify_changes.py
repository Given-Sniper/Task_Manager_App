#!/usr/bin/env python3
"""
Verify the changes made to the upload workflow
"""

import sqlite3
import os

def verify_database_state():
    """Check the current database state"""
    print("=== Database Verification ===")
    
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Check in-progress tasks for DEV001
    cursor.execute('''
        SELECT task_id, title, status, assigned_to 
        FROM tasks 
        WHERE assigned_to = ? AND status = ?
    ''', ('DEV001', 'in_progress'))
    
    in_progress_tasks = cursor.fetchall()
    print(f"In-progress tasks for DEV001: {len(in_progress_tasks)}")
    for task in in_progress_tasks:
        print(f"  {task[0]}: {task[1]} ({task[2]})")
    
    # Check assigned tasks for DEV001
    cursor.execute('''
        SELECT task_id, title, status, assigned_to 
        FROM tasks 
        WHERE assigned_to = ? AND status = ?
    ''', ('DEV001', 'assigned'))
    
    assigned_tasks = cursor.fetchall()
    print(f"\nAssigned tasks for DEV001: {len(assigned_tasks)}")
    for task in assigned_tasks:
        print(f"  {task[0]}: {task[1]} ({task[2]})")
    
    # Check existing submissions
    cursor.execute('SELECT task_id, submit_original_name, submitted_at FROM task_submissions')
    submissions = cursor.fetchall()
    print(f"\nExisting submissions: {len(submissions)}")
    for sub in submissions:
        print(f"  {sub[0]}: {sub[1]} at {sub[2]}")
    
    conn.close()

def verify_template_changes():
    """Verify template changes are correct"""
    print("\n=== Template Changes Verification ===")
    
    # Check developer dashboard template
    with open('templates/developer_dashboard.html', 'r') as f:
        dashboard_content = f.read()
    
    # Check if Details button was removed from assigned tasks
    assigned_section_start = dashboard_content.find('<!-- Assigned Tasks -->')
    in_progress_section_start = dashboard_content.find('<!-- In Progress Tasks -->')
    
    if assigned_section_start != -1 and in_progress_section_start != -1:
        assigned_section = dashboard_content[assigned_section_start:in_progress_section_start]
        
        # Check assigned section doesn't have Details link
        has_details_in_assigned = 'Details' in assigned_section
        print(f"Assigned section has Details button: {has_details_in_assigned}")
        
        # Check in-progress section has upload form
        in_progress_section = dashboard_content[in_progress_section_start:]
        has_upload_form = 'Submit Your Work' in in_progress_section
        has_file_input = 'submission_file' in in_progress_section
        has_submit_button = 'Submit Task with File' in in_progress_section
        
        print(f"In-progress section has upload form: {has_upload_form}")
        print(f"In-progress section has file input: {has_file_input}")
        print(f"In-progress section has submit button: {has_submit_button}")
        
        if not has_details_in_assigned and has_upload_form and has_file_input:
            print("[PASS] Developer dashboard template changes are correct")
        else:
            print("[FAIL] Template changes incomplete")
    
    # Check task details template
    with open('templates/task_details.html', 'r') as f:
        task_details_content = f.read()
    
    # Check submission condition
    has_in_progress_condition = "task.status == 'in_progress'" in task_details_content
    has_info_message = "Tasks can only be submitted when they are in 'In Progress' status" in task_details_content
    
    print(f"Task details has in_progress condition: {has_in_progress_condition}")
    print(f"Task details has updated info message: {has_info_message}")
    
    if has_in_progress_condition and has_info_message:
        print("[PASS] Task details template changes are correct")
    else:
        print("[FAIL] Task details template changes incomplete")

def verify_backend_logic():
    """Verify backend code changes"""
    print("\n=== Backend Logic Verification ===")
    
    with open('main.py', 'r') as f:
        main_content = f.read()
    
    # Check if submission logic only allows in_progress
    has_in_progress_check = "if task.status != 'in_progress':" in main_content
    has_updated_error_msg = "Task must be in progress to submit" in main_content
    
    print(f"Backend has in_progress only check: {has_in_progress_check}")
    print(f"Backend has updated error message: {has_updated_error_msg}")
    
    if has_in_progress_check and has_updated_error_msg:
        print("[PASS] Backend logic changes are correct")
    else:
        print("[FAIL] Backend logic changes incomplete")

def verify_file_structure():
    """Check if required directories exist"""
    print("\n=== File Structure Verification ===")
    
    submission_dir = "instance/uploads/submissions"
    exists = os.path.exists(submission_dir)
    print(f"Submissions directory exists: {exists}")
    
    if exists:
        # Check contents
        try:
            contents = os.listdir(submission_dir)
            print(f"Submissions directory contents: {len(contents)} items")
            for item in contents:
                print(f"  {item}")
        except:
            print("Could not list submissions directory")
    
    if exists:
        print("[PASS] File structure is ready")
    else:
        print("[INFO] Submissions directory will be created on first upload")

if __name__ == "__main__":
    print("Verifying Upload Workflow Changes")
    print("=" * 40)
    
    verify_database_state()
    verify_template_changes()
    verify_backend_logic()
    verify_file_structure()
    
    print("\n" + "=" * 40)
    print("Verification complete. Check output above for any issues.")