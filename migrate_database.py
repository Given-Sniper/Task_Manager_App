#!/usr/bin/env python3
"""
Database migration script to add new ZIP specification fields to tasks table
"""

import sqlite3
from datetime import datetime

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    return column in columns

def migrate_database():
    """Add new spec file columns to tasks table"""
    print("=== DATABASE MIGRATION ===")
    
    try:
        # Connect to database
        conn = sqlite3.connect('task_manager.db')
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(tasks)")
        current_columns = [col[1] for col in cursor.fetchall()]
        print(f"Current columns in tasks table: {len(current_columns)}")
        
        # Define new columns to add
        new_columns = [
            ('spec_zip_path', 'VARCHAR(500)'),
            ('spec_original_name', 'VARCHAR(255)'),
            ('spec_size_bytes', 'INTEGER'),
            ('spec_uploaded_at', 'DATETIME')
        ]
        
        # Add missing columns
        added_columns = 0
        for column_name, column_type in new_columns:
            if not check_column_exists(cursor, 'tasks', column_name):
                try:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {column_type}")
                    print(f"[ADDED] Column: {column_name}")
                    added_columns += 1
                except Exception as e:
                    print(f"[ERROR] Failed to add {column_name}: {str(e)}")
            else:
                print(f"[EXISTS] Column: {column_name}")
        
        # Commit changes
        conn.commit()
        
        # Verify new schema
        cursor.execute("PRAGMA table_info(tasks)")
        updated_columns = [col[1] for col in cursor.fetchall()]
        print(f"\nUpdated columns in tasks table: {len(updated_columns)}")
        
        # Show the new columns
        spec_columns = [col for col in updated_columns if col.startswith('spec_')]
        print(f"Spec-related columns: {spec_columns}")
        
        conn.close()
        
        if added_columns > 0:
            print(f"\n[SUCCESS] Database migration completed. Added {added_columns} new columns.")
        else:
            print(f"\n[INFO] Database already up to date.")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] Database migration failed: {str(e)}")
        return False

def show_table_schema():
    """Display current table schema"""
    try:
        conn = sqlite3.connect('task_manager.db')
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        
        print("\n=== TASKS TABLE SCHEMA ===")
        for col in columns:
            cid, name, type_, notnull, default_val, pk = col
            print(f"{cid:2}: {name:25} {type_:15} {'NOT NULL' if notnull else 'NULL'} {'PK' if pk else ''}")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Could not show schema: {str(e)}")

if __name__ == "__main__":
    print("Database Migration for ZIP Upload Feature")
    print("=" * 40)
    
    # Show current schema
    show_table_schema()
    
    # Perform migration
    success = migrate_database()
    
    # Show updated schema
    if success:
        show_table_schema()
    
    print("\nMigration complete!")