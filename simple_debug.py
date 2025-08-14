#!/usr/bin/env python3
"""
Simple debug of upload issue
"""

import sqlite3

def main():
    print("=== DEBUGGING UPLOAD ISSUE ===")
    
    # Check database state
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Get tasks for DEV001
    cursor.execute('''
        SELECT task_id, title, status 
        FROM tasks 
        WHERE assigned_to = ? 
        ORDER BY status
    ''', ('DEV001',))
    
    tasks = cursor.fetchall()
    print(f"\nTasks for DEV001: {len(tasks)}")
    
    status_counts = {}
    for task in tasks:
        status = task[2]
        status_counts[status] = status_counts.get(status, 0) + 1
        print(f"  {task[0]}: {task[1]} - {task[2]}")
    
    print(f"\nStatus counts: {status_counts}")
    
    # Check if any in_progress
    in_progress_count = status_counts.get('in_progress', 0)
    print(f"In-progress tasks: {in_progress_count}")
    
    if in_progress_count == 0:
        print("PROBLEM: No in-progress tasks!")
        print("SOLUTION: Need to start a task or change status")
        
        # Let's update one assigned task to in_progress
        cursor.execute('SELECT task_id FROM tasks WHERE assigned_to = ? AND status = ? LIMIT 1', ('DEV001', 'assigned'))
        assigned_task = cursor.fetchone()
        
        if assigned_task:
            task_id = assigned_task[0]
            cursor.execute('UPDATE tasks SET status = ? WHERE task_id = ?', ('in_progress', task_id))
            conn.commit()
            print(f"FIXED: Updated {task_id} to in_progress")
        else:
            print("ERROR: No assigned tasks to update")
    else:
        print("GOOD: In-progress tasks exist")
    
    # Check submissions
    cursor.execute('SELECT task_id, submit_original_name FROM task_submissions')
    submissions = cursor.fetchall()
    print(f"\nExisting submissions: {len(submissions)}")
    for sub in submissions:
        print(f"  {sub[0]}: {sub[1]}")
    
    conn.close()
    
    print("\n=== TEMPLATE LOGIC CHECK ===")
    
    # Read and check template
    with open('templates/developer_dashboard.html', 'r') as f:
        content = f.read()
    
    # Check for key elements
    checks = [
        ('In Progress section', 'In Progress Tasks' in content),
        ('Upload form', 'Submit Your Work' in content),
        ('File input', 'submission_file' in content),
        ('ZIP accept', 'accept=".zip"' in content),
        ('Form action', 'submit_task_with_file' in content),
    ]
    
    print("Template checks:")
    for name, result in checks:
        status = "OK" if result else "MISSING"
        print(f"  {name}: {status}")
    
    print("\n=== NEXT STEPS ===")
    print("1. Verify in_progress tasks exist")
    print("2. Check developer dashboard loads correctly")
    print("3. Look for upload form in In Progress section")
    print("4. Test file upload functionality")

if __name__ == "__main__":
    main()