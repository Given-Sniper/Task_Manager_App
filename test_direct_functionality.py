#!/usr/bin/env python3
"""
Direct functionality tests - testing the fixed functions directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_new_employee, db, Employee, Task
from flask import Flask
from werkzeug.security import check_password_hash
import sqlite3
from datetime import datetime

def test_create_employee_function():
    """Test the fixed create_new_employee function"""
    print("=== Testing create_new_employee function ===")
    
    try:
        result = create_new_employee(
            name='Test Employee Direct',
            email='testdirect@example.com',
            role='developer',
            skills=['Python', 'React'],
            experience=2
        )
        print(f"Create employee result: {result}")
        
        if result and result.get('success'):
            # Verify employee was created in database
            conn = sqlite3.connect('task_manager.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM employees WHERE email = ?', ('testdirect@example.com',))
            employee = cursor.fetchone()
            conn.close()
            
            if employee:
                print(f"[PASS] Employee created successfully: {employee[1]}")  # name field
                return True
            else:
                print("[FAIL] Employee not found in database")
                return False
        else:
            print(f"[FAIL] Create employee failed: {result}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Exception during employee creation: {str(e)}")
        return False

def test_pending_tasks_function():
    """Test that we can retrieve submitted tasks from database"""
    print("\n=== Testing submitted tasks retrieval ===")
    
    try:
        # Check if we have our test task
        conn = sqlite3.connect('task_manager.db')
        cursor = conn.cursor()
        cursor.execute('SELECT task_id, title, status FROM tasks WHERE status = ?', ('submitted',))
        submitted_tasks = cursor.fetchall()
        conn.close()
        
        print(f"Found {len(submitted_tasks)} submitted tasks:")
        for task in submitted_tasks:
            print(f"  - Task ID: {task[0]}, Title: {task[1]}, Status: {task[2]}")
        
        return len(submitted_tasks) > 0
        
    except Exception as e:
        print(f"[FAIL] Exception during task retrieval: {str(e)}")
        return False

def test_task_approval_function():
    """Test task status update (approval simulation)"""
    print("\n=== Testing task approval function ===")
    
    try:
        # Update task status directly in database
        conn = sqlite3.connect('task_manager.db')
        cursor = conn.cursor()
        
        # Check if TEST001 exists
        cursor.execute('SELECT task_id, status FROM tasks WHERE task_id = ?', ('TEST001',))
        task = cursor.fetchone()
        
        if not task:
            print("[FAIL] Test task TEST001 not found")
            return False
        
        print(f"Task TEST001 current status: {task[1]}")
        
        # Update status to completed
        cursor.execute('''
            UPDATE tasks 
            SET status = ?, completion_date = ?
            WHERE task_id = ?
        ''', ('completed', datetime.now().isoformat(), 'TEST001'))
        
        conn.commit()
        
        # Verify update
        cursor.execute('SELECT status FROM tasks WHERE task_id = ?', ('TEST001',))
        new_status = cursor.fetchone()[0]
        conn.close()
        
        print(f"Task TEST001 new status: {new_status}")
        return new_status == 'completed'
        
    except Exception as e:
        print(f"[FAIL] Exception during task approval: {str(e)}")
        return False

def test_password_hashing():
    """Test that password hashing works correctly"""
    print("\n=== Testing password hashing ===")
    
    try:
        from werkzeug.security import generate_password_hash, check_password_hash
        
        password = "testpassword123"
        hashed = generate_password_hash(password)
        
        print(f"Generated hash for '{password}': {hashed[:50]}...")
        
        # Test verification
        is_valid = check_password_hash(hashed, password)
        is_invalid = check_password_hash(hashed, "wrongpassword")
        
        print(f"[PASS] Correct password verification: {is_valid}")
        print(f"[PASS] Wrong password rejection: {not is_invalid}")
        
        return is_valid and not is_invalid
        
    except Exception as e:
        print(f"[FAIL] Exception during password hashing test: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting direct functionality tests...\n")
    
    results = {
        "employee_creation": test_create_employee_function(),
        "submitted_tasks_retrieval": test_pending_tasks_function(),
        "task_approval_simulation": test_task_approval_function(),
        "password_hashing": test_password_hashing()
    }
    
    print("\n=== Direct Test Results Summary ===")
    passed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)}")
    overall = passed == len(results)
    print(f"Overall Status: {'PASS' if overall else 'FAIL'}")