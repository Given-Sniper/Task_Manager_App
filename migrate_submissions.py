#!/usr/bin/env python3
"""
Database migration script to add TaskSubmission table for developer submissions
"""

import sqlite3
from datetime import datetime

def create_task_submissions_table():
    """Create the task_submissions table"""
    print("=== CREATING TASK SUBMISSIONS TABLE ===")
    
    try:
        # Connect to database
        conn = sqlite3.connect('task_manager.db')
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_submissions'")
        if cursor.fetchone():
            print("[INFO] task_submissions table already exists")
            conn.close()
            return True
        
        # Create task_submissions table
        cursor.execute('''
            CREATE TABLE task_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id VARCHAR(50) NOT NULL,
                developer_id VARCHAR(50) NOT NULL,
                submit_zip_path VARCHAR(500) NOT NULL,
                submit_original_name VARCHAR(255) NOT NULL,
                submit_size_bytes INTEGER NOT NULL,
                submitted_at DATETIME NOT NULL,
                notes TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks (task_id),
                FOREIGN KEY (developer_id) REFERENCES employees (emp_id)
            )
        ''')
        
        print("[SUCCESS] Created task_submissions table")
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX idx_task_submissions_task_id ON task_submissions (task_id)')
        cursor.execute('CREATE INDEX idx_task_submissions_developer_id ON task_submissions (developer_id)')
        cursor.execute('CREATE INDEX idx_task_submissions_submitted_at ON task_submissions (submitted_at)')
        
        print("[SUCCESS] Created indexes on task_submissions table")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to create task_submissions table: {str(e)}")
        return False

def verify_table_structure():
    """Verify the table was created correctly"""
    try:
        conn = sqlite3.connect('task_manager.db')
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(task_submissions)")
        columns = cursor.fetchall()
        
        print("\n=== TASK SUBMISSIONS TABLE STRUCTURE ===")
        for col in columns:
            cid, name, type_, notnull, default_val, pk = col
            print(f"{cid:2}: {name:25} {type_:15} {'NOT NULL' if notnull else 'NULL'} {'PK' if pk else ''}")
        
        # Check indexes
        cursor.execute("PRAGMA index_list(task_submissions)")
        indexes = cursor.fetchall()
        
        print(f"\nIndexes created: {len(indexes)}")
        for idx in indexes:
            print(f"  - {idx[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Could not verify table structure: {str(e)}")
        return False

def create_submissions_directory():
    """Create the submissions upload directory structure"""
    import os
    
    submissions_dir = "instance/uploads/submissions"
    
    try:
        os.makedirs(submissions_dir, exist_ok=True)
        print(f"[SUCCESS] Created directory: {submissions_dir}")
        return True
    except Exception as e:
        print(f"[ERROR] Could not create directory: {str(e)}")
        return False

if __name__ == "__main__":
    print("Task Submissions Migration")
    print("=" * 40)
    
    # Create table
    table_success = create_task_submissions_table()
    
    # Verify structure
    if table_success:
        verify_success = verify_table_structure()
    else:
        verify_success = False
    
    # Create directory structure
    dir_success = create_submissions_directory()
    
    # Summary
    print(f"\n=== MIGRATION SUMMARY ===")
    print(f"Table creation: {'SUCCESS' if table_success else 'FAILED'}")
    print(f"Structure verification: {'SUCCESS' if verify_success else 'FAILED'}")
    print(f"Directory creation: {'SUCCESS' if dir_success else 'FAILED'}")
    
    if table_success and dir_success:
        print("\n[SUCCESS] Task submissions migration completed successfully!")
        print("Ready to accept developer submissions.")
    else:
        print("\n[ERROR] Migration failed. Please check errors above.")