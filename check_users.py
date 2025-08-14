#!/usr/bin/env python3
"""
Quick script to check what users exist in the database
"""

import os
import sqlite3

# Connect to the database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'task_manager.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query all employees
    cursor.execute("SELECT emp_id, name, email, role FROM employees")
    employees = cursor.fetchall()
    
    print("=== CURRENT DATABASE USERS ===")
    print("-" * 40)
    for emp_id, name, email, role in employees:
        print(f"ID: {emp_id}")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Role: {role}")
        print("-" * 40)
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")