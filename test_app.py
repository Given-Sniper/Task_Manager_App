#!/usr/bin/env python3
"""
Simple test to check if the Flask app starts without errors
"""

import sys
import os

# Add the current directory to path so we can import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import app, db
    print("✓ Successfully imported Flask app")
    
    # Test that the app context works
    with app.app_context():
        print("✓ App context created successfully")
        
        # Test database connection
        from main import Employee, Task
        print("✓ Database models imported successfully")
        
        # Test basic query
        employee_count = Employee.query.count()
        task_count = Task.query.count()
        print(f"✓ Database connection working - Found {employee_count} employees and {task_count} tasks")
        
    print("\n🎉 All tests passed! The application should start successfully.")
    print("💡 To start the app: python main.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Make sure you have:")
    print("  1. Run: python setup_db.py")
    print("  2. Activated virtual environment: venv\\Scripts\\activate")
    print("  3. Installed requirements: pip install -r requirements.txt")