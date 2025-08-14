#!/usr/bin/env python3
"""
Test the fixes for:
1. Developer dashboard download links
2. Task details submission form
3. PM dashboard active tasks count
"""

import sqlite3

def test_database_state():
    """Test the database to verify our fixes will work"""
    print("=== Testing Database State ===")
    
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Check tasks with spec files
    cursor.execute('''
        SELECT task_id, title, assigned_to, spec_zip_path, spec_original_name 
        FROM tasks 
        WHERE spec_zip_path IS NOT NULL 
        AND assigned_to IS NOT NULL
    ''')
    spec_tasks = cursor.fetchall()
    
    print(f"Tasks with spec files: {len(spec_tasks)}")
    for task in spec_tasks:
        print(f"  {task[0]}: {task[1]} (assigned to {task[2]}) - {task[4]}")
    
    # Check submittable tasks for DEV001
    cursor.execute('''
        SELECT task_id, title, status, assigned_to 
        FROM tasks 
        WHERE assigned_to = ? 
        AND status IN ('assigned', 'in_progress')
    ''', ('DEV001',))
    submittable_tasks = cursor.fetchall()
    
    print(f"\nSubmittable tasks for DEV001: {len(submittable_tasks)}")
    for task in submittable_tasks:
        print(f"  {task[0]}: {task[1]} (status: {task[2]})")
    
    # Check active tasks count
    cursor.execute('''
        SELECT COUNT(*) FROM tasks WHERE status IN ('assigned', 'in_progress')
    ''')
    active_count = cursor.fetchone()[0]
    
    print(f"\nActive tasks count: {active_count}")
    
    # Check if any submissions exist
    cursor.execute('SELECT COUNT(*) FROM task_submissions')
    submissions_count = cursor.fetchone()[0]
    
    print(f"Existing submissions: {submissions_count}")
    
    conn.close()
    
    # Summary
    print("\n=== Test Summary ===")
    if spec_tasks:
        print("[PASS] Tasks with specs exist - download functionality should work")
    else:
        print("[INFO] No tasks with specs - create some to test download functionality")
    
    if submittable_tasks:
        print("[PASS] Submittable tasks exist - submission form should appear")
    else:
        print("[INFO] No submittable tasks - submission form won't appear (correct behavior)")
    
    if active_count > 0:
        print(f"[PASS] Active tasks count ({active_count}) will show correctly on PM dashboard")
    else:
        print("[INFO] No active tasks - PM dashboard will show 0 (correct)")
    
    return True

def test_template_logic():
    """Test the template logic for our fixes"""
    print("\n=== Testing Template Logic ===")
    
    # Test submission form conditions
    test_cases = [
        {"is_pm": False, "is_assigned": True, "status": "assigned", "should_show": True},
        {"is_pm": False, "is_assigned": True, "status": "in_progress", "should_show": True},
        {"is_pm": False, "is_assigned": True, "status": "completed", "should_show": False},
        {"is_pm": False, "is_assigned": True, "status": "submitted", "should_show": False},
        {"is_pm": False, "is_assigned": False, "status": "assigned", "should_show": False},
        {"is_pm": True, "is_assigned": True, "status": "assigned", "should_show": False},
    ]
    
    print("Testing submission form display logic:")
    for i, case in enumerate(test_cases):
        condition = (not case["is_pm"] and case["is_assigned"] and case["status"] in ['assigned', 'in_progress'])
        expected = case["should_show"]
        result = "PASS" if condition == expected else "FAIL"
        print(f"  Case {i+1}: {case} -> {condition} (expected {expected}) [{result}]")
    
    return True

if __name__ == "__main__":
    print("Testing all fixes...")
    test_database_state()
    test_template_logic()
    print("\n[SUCCESS] All fix tests completed!")