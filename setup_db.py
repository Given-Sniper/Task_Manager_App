#!/usr/bin/env python3
"""
Database Setup Script for Task Manager App
Creates tables and initial data with SQLite support
"""

import os
import sys
import string
import random
from datetime import datetime, timedelta

def generate_random_password(length=8):
    """Generate a random password with the specified length"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def setup_database():
    """Initialize the database with tables and sample data"""
    
    try:
        # Import Flask app components
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from werkzeug.security import generate_password_hash
        
        # Create Flask app for database setup
        app = Flask(__name__)
        
        # Configure SQLite database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'task_manager.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'setup-key'
        
        # Initialize database
        db = SQLAlchemy(app)
        
        # Define Employee Model
        class Employee(db.Model):
            __tablename__ = 'employees'
            
            emp_id = db.Column(db.String(50), primary_key=True)
            name = db.Column(db.String(100), nullable=False)
            email = db.Column(db.String(100), nullable=False, unique=True)
            password_hash = db.Column(db.String(255), nullable=False)
            is_first_login = db.Column(db.Boolean, default=True)
            role = db.Column(db.String(20), nullable=False)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            last_login = db.Column(db.DateTime, nullable=True)
            
            # Additional fields for app functionality
            skills = db.Column(db.Text, default='[]')  # JSON string for SQLite compatibility
            experience = db.Column(db.Integer, default=0)
            tasks_completed = db.Column(db.Integer, default=0)
            success_rate = db.Column(db.Float, default=0.0)
            avatar_url = db.Column(db.String(255), nullable=True)
            
            def set_password(self, password):
                self.password_hash = generate_password_hash(password)
            
            def __repr__(self):
                return f'<Employee {self.emp_id}: {self.name}>'
        
        # Define Task Model
        class Task(db.Model):
            __tablename__ = 'tasks'
            
            task_id = db.Column(db.String(50), primary_key=True)
            title = db.Column(db.String(200), nullable=False)
            description = db.Column(db.Text, nullable=True)
            project_type = db.Column(db.String(50), nullable=False)
            complexity = db.Column(db.String(20), default='Medium')
            priority = db.Column(db.String(20), default='Medium')
            status = db.Column(db.String(30), default='assigned')
            
            # Assignment details
            assigned_to = db.Column(db.String(50), db.ForeignKey('employees.emp_id'), nullable=True)
            assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
            assigned_by = db.Column(db.String(50), nullable=True)
            
            # Task lifecycle
            start_date = db.Column(db.DateTime, nullable=True)
            due_date = db.Column(db.DateTime, nullable=True)
            completion_date = db.Column(db.DateTime, nullable=True)
            submitted_at = db.Column(db.DateTime, nullable=True)
            
            # Evaluation
            success_rating = db.Column(db.Integer, nullable=True)
            feedback = db.Column(db.Text, nullable=True)
            
            # ZIP specification file (PM uploads)
            spec_zip_path = db.Column(db.String(500), nullable=True)  # Relative path to spec ZIP
            spec_original_name = db.Column(db.String(255), nullable=True)  # Original filename
            spec_size_bytes = db.Column(db.Integer, nullable=True)  # File size in bytes
            spec_uploaded_at = db.Column(db.DateTime, nullable=True)  # Upload timestamp
            
            # Developer submission file
            submission_file_path = db.Column(db.String(500), nullable=True)  # Developer uploads submission
            submission_file_name = db.Column(db.String(255), nullable=True)  # Original filename for submission
            
            # Metadata
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            updated_at = db.Column(db.DateTime, default=datetime.utcnow)
            
            def __repr__(self):
                return f'<Task {self.task_id}: {self.title}>'
        
        # Define Notification Model
        class Notification(db.Model):
            __tablename__ = 'notifications'
            
            id = db.Column(db.Integer, primary_key=True)
            emp_id = db.Column(db.String(50), db.ForeignKey('employees.emp_id'), nullable=False)
            task_id = db.Column(db.String(50), db.ForeignKey('tasks.task_id'), nullable=True)
            type = db.Column(db.String(50), nullable=False)  # task_assigned, task_started, task_completed, etc.
            message = db.Column(db.Text, nullable=False)
            is_read = db.Column(db.Boolean, default=False)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            
            def __repr__(self):
                return f'<Notification {self.id}: {self.type}>'
        
        # Create application context and set up database
        with app.app_context():
            print("Creating database tables...")
            
            # Drop existing tables if they exist
            db.drop_all()
            
            # Create all tables
            db.create_all()
            print("[SUCCESS] Database tables created successfully!")
            
            # Create sample employees
            employees_data = [
                {
                    'emp_id': 'ADMIN001',
                    'name': 'System Administrator',
                    'email': 'admin@example.com',
                    'password': 'admin123',
                    'role': 'admin',
                    'skills': '["System Administration", "Database Management", "Security"]',
                    'experience': 5,
                    'tasks_completed': 25,
                    'success_rate': 95.0
                },
                {
                    'emp_id': 'PM001',
                    'name': 'Project Manager',
                    'email': 'manager@example.com',
                    'password': 'manager123',
                    'role': 'project manager',
                    'skills': '["Project Management", "Team Leadership", "Agile", "Scrum"]',
                    'experience': 7,
                    'tasks_completed': 40,
                    'success_rate': 88.5
                },
                {
                    'emp_id': 'DEV001',
                    'name': 'Senior Developer',
                    'email': 'developer@example.com',
                    'password': 'dev123',
                    'role': 'developer',
                    'skills': '["Python", "JavaScript", "React", "Flask", "SQL"]',
                    'experience': 4,
                    'tasks_completed': 60,
                    'success_rate': 92.0
                },
                {
                    'emp_id': 'DEV002',
                    'name': 'Alice Johnson',
                    'email': 'alice@example.com',
                    'password': 'alice123',
                    'role': 'developer',
                    'skills': '["Java", "Spring Boot", "Angular", "MySQL"]',
                    'experience': 3,
                    'tasks_completed': 35,
                    'success_rate': 85.0
                },
                {
                    'emp_id': 'DEV003',
                    'name': 'Bob Wilson',
                    'email': 'bob@example.com',
                    'password': 'bob123',
                    'role': 'developer',
                    'skills': '["C#", ".NET", "Azure", "SQL Server"]',
                    'experience': 2,
                    'tasks_completed': 20,
                    'success_rate': 78.0
                }
            ]
            
            print("Creating sample employees...")
            for emp_data in employees_data:
                employee = Employee(
                    emp_id=emp_data['emp_id'],
                    name=emp_data['name'],
                    email=emp_data['email'],
                    role=emp_data['role'],
                    skills=emp_data['skills'],
                    experience=emp_data['experience'],
                    tasks_completed=emp_data['tasks_completed'],
                    success_rate=emp_data['success_rate'],
                    is_first_login=False
                )
                employee.set_password(emp_data['password'])
                db.session.add(employee)
            
            # Create sample tasks
            sample_tasks = [
                {
                    'task_id': 'TASK001',
                    'title': 'Implement User Authentication',
                    'description': 'Create secure login system with role-based access control',
                    'project_type': 'website_development',
                    'complexity': 'High',
                    'priority': 'High',
                    'status': 'assigned',
                    'assigned_to': 'DEV001',
                    'assigned_by': 'PM001',
                    'due_date': datetime.now() + timedelta(days=7)
                },
                {
                    'task_id': 'TASK002',
                    'title': 'Design Database Schema',
                    'description': 'Create normalized database design for task management',
                    'project_type': 'website_development',
                    'complexity': 'Medium',
                    'priority': 'High',
                    'status': 'in_progress',
                    'assigned_to': 'DEV002',
                    'assigned_by': 'PM001',
                    'start_date': datetime.now() - timedelta(days=2),
                    'due_date': datetime.now() + timedelta(days=3)
                },
                {
                    'task_id': 'TASK003',
                    'title': 'Create REST API Documentation',
                    'description': 'Document all API endpoints with examples',
                    'project_type': 'website_development',
                    'complexity': 'Low',
                    'priority': 'Medium',
                    'status': 'completed',
                    'assigned_to': 'DEV003',
                    'assigned_by': 'PM001',
                    'start_date': datetime.now() - timedelta(days=5),
                    'completion_date': datetime.now() - timedelta(days=1),
                    'success_rating': 4,
                    'due_date': datetime.now() - timedelta(days=1)
                }
            ]
            
            print("Creating sample tasks...")
            for task_data in sample_tasks:
                task = Task(**task_data)
                db.session.add(task)
            
            # Create sample notifications
            sample_notifications = [
                {
                    'emp_id': 'DEV001',
                    'task_id': 'TASK001',
                    'type': 'task_assigned',
                    'message': 'New task assigned: Implement User Authentication',
                    'is_read': False
                },
                {
                    'emp_id': 'DEV002',
                    'task_id': 'TASK002',
                    'type': 'task_started',
                    'message': 'Task started: Design Database Schema',
                    'is_read': False
                },
                {
                    'emp_id': 'DEV003',
                    'task_id': 'TASK003',
                    'type': 'task_completed',
                    'message': 'Task completed: Create REST API Documentation',
                    'is_read': True
                }
            ]
            
            print("Creating sample notifications...")
            for notif_data in sample_notifications:
                notification = Notification(**notif_data)
                db.session.add(notification)
            
            # Commit all changes
            db.session.commit()
            print("[SUCCESS] Sample data created successfully!")
            
            print("\n" + "="*50)
            print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
            print("="*50)
            print("\n[LOGIN CREDENTIALS]")
            print("-" * 30)
            print("Admin:")
            print("   Email: admin@example.com")
            print("   Password: admin123")
            print("\nProject Manager:")
            print("   Email: manager@example.com") 
            print("   Password: manager123")
            print("\nDeveloper:")
            print("   Email: developer@example.com")
            print("   Password: dev123")
            print("\n[NEXT STEPS]")
            print("Start the application with: python main.py")
            print("Access at: http://localhost:5000")
            print("="*50)
            
    except ImportError as e:
        print(f"[ERROR] Import Error: {e}")
        print("Make sure Flask and Flask-SQLAlchemy are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    setup_database()