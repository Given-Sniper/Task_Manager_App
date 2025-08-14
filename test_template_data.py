#!/usr/bin/env python3
"""
Test what data is being passed to the template
"""

import sqlite3
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import get_developer_tasks, app

def test_template_data():
    print("=== TESTING TEMPLATE DATA ===")
    
    # Create application context
    with app.app_context():
        # Get tasks the same way the dashboard route does
        assigned_tasks = get_developer_tasks('DEV001')
    
    print(f"Total assigned_tasks: {len(assigned_tasks)}")
    
    # Categorize tasks the same way the dashboard does
    in_progress_tasks = [task for task in assigned_tasks if task.get('status') == 'in_progress']
    pending_tasks = [task for task in assigned_tasks if task.get('status') == 'assigned']
    pending_approval_tasks = [task for task in assigned_tasks if task.get('status') == 'submitted']
    completed_tasks = [task for task in assigned_tasks if task.get('status') == 'completed']
    
    print(f"In progress tasks: {len(in_progress_tasks)}")
    print(f"Pending tasks: {len(pending_tasks)}")
    print(f"Pending approval: {len(pending_approval_tasks)}")
    print(f"Completed tasks: {len(completed_tasks)}")
    
    print("\n=== IN PROGRESS TASKS DETAILS ===")
    for task in in_progress_tasks:
        print(f"Task: {task.get('task_id')}")
        print(f"  Title: {task.get('title')}")
        print(f"  Status: {task.get('status')}")
        print(f"  Has spec file: {task.get('has_spec_file', False)}")
        print()
    
    if len(in_progress_tasks) > 0:
        print("GOOD: In-progress tasks exist for template")
        print("The upload form should be visible in the dashboard")
    else:
        print("PROBLEM: No in-progress tasks found in template data")
        print("This explains why upload form is not showing")
    
    # Also test the database directly to compare
    print("\n=== DIRECT DATABASE CHECK ===")
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    cursor.execute('SELECT task_id, title, status FROM tasks WHERE assigned_to = ? AND status = ?', ('DEV001', 'in_progress'))
    db_tasks = cursor.fetchall()
    conn.close()
    
    print(f"Direct DB in_progress tasks: {len(db_tasks)}")
    for task in db_tasks:
        print(f"  {task[0]}: {task[1]} - {task[2]}")
    
    if len(db_tasks) != len(in_progress_tasks):
        print("MISMATCH: Database vs get_developer_tasks function results differ!")
    else:
        print("MATCH: Database and function results are consistent")

if __name__ == "__main__":
    test_template_data()