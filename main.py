# main_app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import os
import requests
import json
import zipfile
from dotenv import load_dotenv
from email_services import send_credentials_email
from datetime import datetime, timedelta
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'instance/uploads'
ALLOWED_EXTENSIONS = {'zip'}  # Only ZIP files allowed

# Create upload directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Database configuration for local authentication
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'task_manager.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define Employee Model (same as in setup_db.py)
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
    
    # Additional fields
    skills = db.Column(db.Text, default='[]')
    experience = db.Column(db.Integer, default=0)
    tasks_completed = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    avatar_url = db.Column(db.String(255), nullable=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_skills_list(self):
        """Parse skills JSON string to list"""
        try:
            return json.loads(self.skills) if self.skills else []
        except:
            return []
    
    def set_skills_list(self, skills_list):
        """Set skills list as JSON string"""
        import json
        self.skills = json.dumps(skills_list) if skills_list else '[]'
    
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
    
    def to_dict(self):
        """Convert task to dictionary for JSON serialization"""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'project_type': self.project_type,
            'complexity': self.complexity,
            'priority': self.priority,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'assigned_by': self.assigned_by,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'success_rating': self.success_rating,
            'feedback': self.feedback,
            'spec_zip_path': self.spec_zip_path,
            'spec_original_name': self.spec_original_name,
            'spec_size_bytes': self.spec_size_bytes,
            'spec_uploaded_at': self.spec_uploaded_at.isoformat() if self.spec_uploaded_at else None,
            'submission_file_path': self.submission_file_path,
            'submission_file_name': self.submission_file_name,
            'has_spec_file': self.spec_zip_path is not None,
            'has_submission_file': self.submission_file_path is not None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Task {self.task_id}: {self.title}>'

# Define TaskSubmission Model
class TaskSubmission(db.Model):
    __tablename__ = 'task_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(50), db.ForeignKey('tasks.task_id'), nullable=False)
    developer_id = db.Column(db.String(50), db.ForeignKey('employees.emp_id'), nullable=False)
    
    # File metadata
    submit_zip_path = db.Column(db.String(500), nullable=False)  # Relative path
    submit_original_name = db.Column(db.String(255), nullable=False)
    submit_size_bytes = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Optional notes from developer
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    task = db.relationship('Task', backref='submissions')
    developer = db.relationship('Employee', backref='submissions')
    
    def to_dict(self):
        """Convert submission to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'developer_id': self.developer_id,
            'submit_zip_path': self.submit_zip_path,
            'submit_original_name': self.submit_original_name,
            'submit_size_bytes': self.submit_size_bytes,
            'submitted_at': self.submitted_at.isoformat(),
            'notes': self.notes,
            'developer_name': self.developer.name if self.developer else 'Unknown'
        }
    
    def __repr__(self):
        return f'<TaskSubmission {self.id}: {self.task_id} by {self.developer_id}>'

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

# Employee service configuration
EMPLOYEE_SERVICE_URL = os.environ.get('EMPLOYEE_SERVICE_URL', 'http://localhost:5001/api')
API_KEY = os.environ.get('API_KEY', 'dev_api_key')
PROJECT_TYPES = {
    "website_development": ["HTML", "CSS", "JavaScript", "React", "Vue", "Angular"],
    "mobile_app_development": ["Swift", "Kotlin", "React Native", "Flutter"],
    "machine_learning": ["Python", "TensorFlow", "PyTorch", "Scikit-learn"],
    
}

TASK_SERVICE_URL = os.environ.get('TASK_SERVICE_URL', 'http://localhost:5002/api')

def assign_tasks(tasks):
    response = requests.post(
        f'{TASK_SERVICE_URL}/task-service/assign-tasks',
        json={'tasks': tasks},
        headers=api_headers()
    )
    if response.status_code == 200:
        return response.json()
    return None

def get_project_types():
    """Get all project types from task service with fallback to local definition"""
    try:
        response = requests.get(
            f'{TASK_SERVICE_URL}/task-service/project-types',
            headers=api_headers()
        )
        if response.status_code == 200:
            return response.json().get('project_types', []), response.json().get('project_type_details', {})
        return list(PROJECT_TYPES.keys()), PROJECT_TYPES
    except Exception as e:
        print(f"Error fetching project types: {str(e)}")
        return list(PROJECT_TYPES.keys()), PROJECT_TYPES

def get_skills_for_project_type(project_type):
    """Get required skills for a specific project type"""
    try:
        response = requests.get(
            f'{TASK_SERVICE_URL}/task-service/skills-for-project',
            params={'project_type': project_type},
            headers=api_headers()
        )
        if response.status_code == 200:
            return response.json().get('skills', [])
        return PROJECT_TYPES.get(project_type, [])
    except Exception as e:
        print(f"Error fetching skills for project type: {str(e)}")
        return PROJECT_TYPES.get(project_type, [])


def format_date(date_str, format_str='%b %d, %Y'):
    """Format a date string with the specified format"""
    if not date_str:
        return "N/A"
    
    try:
        # First try to parse the date string
        if isinstance(date_str, str):
            # Try ISO format first (most common API response format)
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                # Try common date formats
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        except ValueError:
                            return date_str  # Return original if parsing fails
        elif isinstance(date_str, datetime):
            date_obj = date_str
        else:
            return str(date_str)
        
        # Format the date object
        return date_obj.strftime(format_str)
    except Exception as e:
        print(f"Error formatting date: {str(e)}")
        return str(date_str)  # Return original as fallback

def get_developer_tasks(emp_id):
    """Get all tasks assigned to a specific developer from local database"""
    try:
        tasks = Task.query.filter_by(assigned_to=emp_id).all()
        task_list = []
        
        for task in tasks:
            task_dict = {
                'task_id': task.task_id,
                'title': task.title,
                'description': task.description,
                'project_type': task.project_type,
                'complexity': task.complexity,
                'priority': task.priority,
                'status': task.status,
                'assigned_to': task.assigned_to,
                'assigned_by': task.assigned_by,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'start_date': task.start_date.isoformat() if task.start_date else None,
                'completion_date': task.completion_date.isoformat() if task.completion_date else None,
                'submitted_at': task.submitted_at.isoformat() if task.submitted_at else None,
                'success_rating': task.success_rating,
                'feedback': task.feedback,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                # Spec file metadata
                'spec_zip_path': task.spec_zip_path,
                'spec_original_name': task.spec_original_name,
                'spec_size_bytes': task.spec_size_bytes,
                'spec_uploaded_at': task.spec_uploaded_at.isoformat() if task.spec_uploaded_at else None,
                'has_spec_file': task.spec_zip_path is not None
            }
            task_list.append(task_dict)
        
        return task_list
    except Exception as e:
        print(f"Error fetching developer tasks: {str(e)}")
        return []

# Helper functions for API calls
def api_headers():
    key = os.environ.get('API_KEY', 'dev_api_key')
    print(f"Using API key: {key}")  # Debug line
    return {'X-API-KEY': key, 'Content-Type': 'application/json'}

def get_employee(emp_id):
    """Get employee from local database"""
    try:
        employee = Employee.query.filter(
            (Employee.email == emp_id) | (Employee.emp_id == emp_id)
        ).first()
        
        if employee:
            return {
                'emp_id': employee.emp_id,
                'name': employee.name,
                'email': employee.email,
                'role': employee.role,
                'skills': employee.get_skills_list(),
                'experience': employee.experience,
                'tasks_completed': employee.tasks_completed,
                'success_rate': employee.success_rate,
                'is_first_login': employee.is_first_login,
                'created_at': employee.created_at.isoformat() if employee.created_at else None,
                'last_login': employee.last_login.isoformat() if employee.last_login else None
            }
        return None
    except Exception as e:
        print(f"Error getting employee: {str(e)}")
        return None

def authenticate_employee(emp_id, password):
    """Authenticate employee using local database"""
    print(f"Attempting local authentication for emp_id: {emp_id}")
    
    try:
        # Try to authenticate with email first, then emp_id
        employee = Employee.query.filter(
            (Employee.email == emp_id) | (Employee.emp_id == emp_id)
        ).first()
        
        if employee and employee.check_password(password):
            print(f"Authentication successful for {employee.name}")
            # Update last login
            employee.last_login = datetime.utcnow()
            db.session.commit()
            
            return {
                'authenticated': True,
                'employee': {
                    'emp_id': employee.emp_id,
                    'name': employee.name,
                    'email': employee.email,
                    'role': employee.role,
                    'skills': employee.get_skills_list(),
                    'experience': employee.experience,
                    'tasks_completed': employee.tasks_completed,
                    'success_rate': employee.success_rate,
                    'is_first_login': employee.is_first_login,
                    'created_at': employee.created_at.isoformat() if employee.created_at else None,
                    'last_login': employee.last_login.isoformat() if employee.last_login else None
                }
            }
        else:
            print(f"Authentication failed for emp_id: {emp_id}")
            return {'authenticated': False, 'reason': 'Invalid credentials'}
            
    except Exception as e:
        print(f"Exception during local authentication: {str(e)}")
        return {'authenticated': False, 'reason': f'Database error: {str(e)}'}

def change_employee_password(emp_id, current_password, new_password):
    """Change employee password using local database"""
    try:
        # Get employee from local database
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        
        if not employee:
            return {'success': False, 'error': 'Employee not found'}
        
        # Verify current password
        if not employee.check_password(current_password):
            return {'success': False, 'error': 'Current password is incorrect'}
        
        # Set new password
        employee.set_password(new_password)
        
        # Update first_login status if it was a first login
        if employee.is_first_login:
            employee.is_first_login = False
        
        # Save changes
        db.session.commit()
        
        return {'success': True, 'message': 'Password changed successfully'}
        
    except Exception as e:
        db.session.rollback()
        print(f"Error changing password for {emp_id}: {str(e)}")
        return {'success': False, 'error': 'Failed to change password'}

def get_all_employees():
    """Get all employees from local database"""
    try:
        employees = Employee.query.all()
        return [{
            'emp_id': emp.emp_id,
            'name': emp.name,
            'email': emp.email,
            'role': emp.role,
            'skills': emp.get_skills_list(),
            'experience': emp.experience,
            'tasks_completed': emp.tasks_completed,
            'success_rate': emp.success_rate,
            'created_at': emp.created_at.isoformat() if emp.created_at else None
        } for emp in employees]
    except Exception as e:
        print(f"Error getting all employees: {str(e)}")
        return []

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename_custom(filename):
    """Create secure filename"""
    import re
    import unicodedata
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename

def save_uploaded_file(file, task_id, file_type='task'):
    """Save uploaded file and return path and original name"""
    if file and allowed_file(file.filename):
        # Create unique filename with task_id and timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{task_id}_{file_type}_{timestamp}_{secure_filename_custom(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            return filepath, file.filename
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return None, None
    return None, None

def validate_zip_file(file):
    """Validate that uploaded file is a real ZIP file"""
    if not file or not allowed_file(file.filename):
        return False, "Only .zip files are allowed"
    
    # Check if it's a valid ZIP file using zipfile.is_zipfile()
    if not zipfile.is_zipfile(file):
        return False, "File is not a valid ZIP archive"
    
    return True, "Valid ZIP file"

def save_spec_file(file, task_id):
    """Save specification ZIP file with organized directory structure"""
    if not file:
        return None, None, None
    
    # Validate ZIP file
    is_valid, error_msg = validate_zip_file(file)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Create timestamp and secure filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    safe_name = secure_filename_custom(file.filename)
    filename = f"{timestamp}_{safe_name}"
    
    # Create task-specific directory: instance/uploads/tasks/<task_id>/
    task_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'tasks', task_id)
    os.makedirs(task_dir, exist_ok=True)
    
    # Full file path
    filepath = os.path.join(task_dir, filename)
    
    try:
        # Save file
        file.save(filepath)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        # Return relative path for database storage
        relative_path = os.path.relpath(filepath)
        
        return relative_path, file.filename, file_size
    except Exception as e:
        print(f"Error saving spec file: {str(e)}")
        # Clean up if file was partially created
        if os.path.exists(filepath):
            os.remove(filepath)
        raise

def save_submission_file(file, task_id):
    """Save developer submission ZIP file with organized directory structure"""
    if not file:
        return None, None, None
    
    # Validate ZIP file
    is_valid, error_msg = validate_zip_file(file)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Create timestamp and secure filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    safe_name = secure_filename_custom(file.filename)
    filename = f"{timestamp}_{safe_name}"
    
    # Create task-specific directory: instance/uploads/submissions/<task_id>/
    submission_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'submissions', task_id)
    os.makedirs(submission_dir, exist_ok=True)
    
    # Full file path
    filepath = os.path.join(submission_dir, filename)
    
    try:
        # Save file
        file.save(filepath)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        # Return relative path for database storage
        relative_path = os.path.relpath(filepath)
        
        return relative_path, file.filename, file_size
    except Exception as e:
        print(f"Error saving submission file: {str(e)}")
        # Clean up if file was partially created
        if os.path.exists(filepath):
            os.remove(filepath)
        raise

def get_active_tasks_count(emp_id):
    """Get count of active tasks for an employee (assigned or in_progress)"""
    try:
        active_count = Task.query.filter(
            Task.assigned_to == emp_id,
            Task.status.in_(['assigned', 'in_progress'])
        ).count()
        return active_count
    except Exception as e:
        print(f"Error getting active tasks count for {emp_id}: {str(e)}")
        return 0

def get_task_assignment_recommendation(task_data):
    """Get the best employee recommendation for a task"""
    try:
        # Get all developers (only developers can be assigned tasks)
        developers = Employee.query.filter_by(role='developer').all()
        
        if not developers:
            return None
            
        required_skills = task_data.get('skills', [])
        best_match = None
        best_score = 0
        
        for dev in developers:
            # Check task limit (max 3 active tasks)
            active_tasks = get_active_tasks_count(dev.emp_id)
            if active_tasks >= 3:
                print(f"Developer {dev.name} ({dev.emp_id}) has {active_tasks} active tasks - skipping")
                continue
            
            dev_skills = dev.get_skills_list()
            
            # Calculate skill match percentage
            if required_skills:
                matching_skills = len([skill for skill in required_skills if skill in dev_skills])
                skill_match = (matching_skills / len(required_skills)) * 100
            else:
                skill_match = 50  # Default score if no skills specified
            
            # Apply 50% minimum skill match requirement
            if skill_match < 50:
                print(f"Developer {dev.name} ({dev.emp_id}) has {skill_match:.1f}% skill match - below 50% minimum")
                continue
            
            # Calculate overall score (skill match + experience + success rate)
            experience_score = min(dev.experience * 10, 50)  # Cap at 50
            success_score = dev.success_rate * 0.5  # Max 50 from success rate
            
            total_score = skill_match + experience_score + success_score
            
            if total_score > best_score:
                best_score = total_score
                best_match = {
                    'emp_id': dev.emp_id,
                    'name': dev.name,
                    'skill_match_percentage': f"{skill_match:.1f}%",
                    'match_score': f"{total_score:.1f}",
                    'skills': dev_skills,
                    'active_tasks': active_tasks
                }
        
        return best_match
        
    except Exception as e:
        print(f"Error getting task assignment recommendation: {str(e)}")
        return None

def get_faq_content(user_role):
    """Get role-specific FAQ content"""
    faq_data = {
        'developer': [
            {
                'question': 'How do I start working on a task?',
                'answer': 'Click the "Start Task" button on any assigned task to move it to in-progress status.'
            },
            {
                'question': 'How do I submit a task for review?',
                'answer': 'Once you complete a task, click the "Submit" button to send it for project manager approval.'
            },
            {
                'question': 'How can I view my task performance?',
                'answer': 'Check the performance chart on your dashboard to see your success rate and completion trends.'
            },
            {
                'question': 'How do I update my skills profile?',
                'answer': 'Click the "Add Skills" button in the Quick Actions section. Contact your administrator for profile updates.'
            }
        ],
        'project manager': [
            {
                'question': 'How do I create and assign a new task?',
                'answer': 'Click on any project type card, fill in the task details, and click "Get Recommendation" to find the best developer for the task.'
            },
            {
                'question': 'How do I review submitted tasks?',
                'answer': 'Check the "Tasks Submitted for Approval" section and click the "Review" button to approve or reject tasks.'
            },
            {
                'question': 'How do I view team performance?',
                'answer': 'Check the stats cards at the top and the "Top Performers" section to see team metrics and individual performance.'
            },
            {
                'question': 'What does the recommendation system consider?',
                'answer': 'The system considers skill match, employee experience, past success rate, and current workload to recommend the best person for each task.'
            }
        ],
        'admin': [
            {
                'question': 'How do I create a new employee account?',
                'answer': 'Click the "Create Employee" button at the top right of the dashboard and fill in the employee details.'
            },
            {
                'question': 'How do I update employee metrics?',
                'answer': 'Click the "Metrics" button next to any employee to update their tasks completed and success rate.'
            },
            {
                'question': 'How do I filter and search employees?',
                'answer': 'Use the filters section above the employee table to filter by role, experience, or search by name, email, or skills.'
            },
            {
                'question': 'How do I view system statistics?',
                'answer': 'The stats cards at the top show total employees, role distribution, average experience, success rate, and total completed tasks.'
            }
        ]
    }
    
    return faq_data.get(user_role, [])

def get_pending_tasks():
    """Get all tasks that are submitted and waiting for approval"""
    try:
        # Query tasks with 'submitted' status from the local database
        pending_tasks = Task.query.filter_by(status='submitted').all()
        
        # Convert to list of dictionaries with employee info
        task_list = []
        for task in pending_tasks:
            # Get employee info for the task
            employee = Employee.query.filter_by(emp_id=task.assigned_to).first()
            
            task_dict = {
                'task_id': task.task_id,
                'title': task.title,
                'description': task.description,
                'project_type': task.project_type,
                'complexity': task.complexity,
                'priority': task.priority,
                'status': task.status,
                'assigned_to': task.assigned_to,
                'assigned_to_name': employee.name if employee else 'Unknown',
                'submitted_at': task.submitted_at.isoformat() if task.submitted_at else None,
                'due_date': task.due_date.isoformat() if task.due_date else None
            }
            task_list.append(task_dict)
        
        return task_list
        
    except Exception as e:
        print(f"Error getting pending tasks: {str(e)}")
        return []

def create_new_employee(name, email, role, skills=None, experience=None, emp_id=None):
    """Create a new employee using local database"""
    try:
        # Check if employee with same email already exists
        existing_employee = Employee.query.filter_by(email=email).first()
        if existing_employee:
            return False, "Employee with this email already exists"
        
        # Generate emp_id if not provided
        if not emp_id:
            # Generate unique emp_id based on role
            role_prefix = role.upper()[:3] if role else "EMP"
            # Find highest existing ID for this role
            existing_ids = Employee.query.filter(Employee.emp_id.like(f"{role_prefix}%")).all()
            if existing_ids:
                max_num = 0
                for emp in existing_ids:
                    try:
                        num_part = int(emp.emp_id[3:])
                        max_num = max(max_num, num_part)
                    except:
                        pass
                emp_id = f"{role_prefix}{str(max_num + 1).zfill(3)}"
            else:
                emp_id = f"{role_prefix}001"
        
        # Check if emp_id already exists
        existing_emp_id = Employee.query.filter_by(emp_id=emp_id).first()
        if existing_emp_id:
            return False, "Employee ID already exists"
        
        # Create new employee
        new_employee = Employee(
            emp_id=emp_id,
            name=name,
            email=email,
            role=role,
            experience=experience or 0,
            tasks_completed=0,
            success_rate=0.0,
            is_first_login=True
        )
        
        # Set default password based on role
        if role.lower() == 'developer':
            default_password = 'developer123'
        else:
            default_password = 'password123'
        
        new_employee.set_password(default_password)
        
        # Set skills if provided
        if skills:
            if isinstance(skills, str):
                # If skills is a string, try to parse as JSON
                import json
                try:
                    skills_list = json.loads(skills)
                except:
                    skills_list = [skills]  # Treat as single skill
            else:
                skills_list = skills
            new_employee.set_skills_list(skills_list)
        
        # Add to database
        db.session.add(new_employee)
        db.session.commit()
        
        # Send email with login credentials
        try:
            send_credentials_email(
                email=email,
                emp_id=emp_id,
                temp_password=default_password  # Use the same password we set
            )
            print(f"Login credentials email sent to {email} with password: {default_password}")
        except Exception as e:
            print(f"Failed to send email to {email}: {str(e)}")
            # Don't fail the whole operation if email fails
        
        return True, emp_id
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating employee: {str(e)}")
        return False, f"Failed to create employee: {str(e)}"

def update_employee(emp_id, data):
    """Update employee using local database"""
    try:
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return None
        
        # Update allowed fields
        if 'name' in data:
            employee.name = data['name']
        if 'email' in data:
            employee.email = data['email']
        if 'role' in data:
            employee.role = data['role']
        if 'experience' in data:
            employee.experience = data['experience']
        if 'tasks_completed' in data:
            employee.tasks_completed = data['tasks_completed']
        if 'success_rate' in data:
            employee.success_rate = data['success_rate']
        if 'skills' in data:
            employee.set_skills_list(data['skills'])
        
        db.session.commit()
        
        return {
            'success': True,
            'employee': {
                'emp_id': employee.emp_id,
                'name': employee.name,
                'email': employee.email,
                'role': employee.role
            }
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating employee {emp_id}: {str(e)}")
        return None

def delete_employee(emp_id):
    """Delete employee using local database"""
    try:
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return False
        
        # Also delete any tasks assigned to this employee
        Task.query.filter_by(assigned_to=emp_id).delete()
        
        # Delete the employee
        db.session.delete(employee)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting employee {emp_id}: {str(e)}")
        return False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin_login_page():
    """Special route for admin login that bypasses role selection"""
    return render_template("admin_login.html")

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        password = request.form.get('password')
        
        # Attempt authentication
        result = authenticate_employee(emp_id, password)
        
        if not result['authenticated']:
            flash('Invalid employee ID or password')
            return render_template('admin_login.html')
        
        employee = result['employee']
        
        if employee['role'] != 'admin':
            flash('This employee ID is not registered as an admin')
            return render_template('admin_login.html')
        
        # Store employee info in session
        session['emp_id'] = emp_id
        session['role'] = employee['role']
        session['name'] = employee['name']
        session['email'] = employee['email']
        
        # If first login, redirect to password change page
        if employee['is_first_login']:
            return redirect(url_for('change_password'))
        
        # Direct to admin dashboard
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_login.html')

@app.route('/select_role/<role>')
def select_role(role):
    if role not in ['developer', 'project_manager', 'human_resource']:
        flash('Invalid role selected')
        return redirect(url_for('index'))
    
    session['selected_role'] = role
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'selected_role' not in session:
        flash('Please select a role first')
        return redirect(url_for('index'))
    
    role = session['selected_role']
    print(f"\n--- LOGIN ATTEMPT ---\nRole selected: {role}")

    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        password = request.form.get('password')
        print(f"Attempting login for: {emp_id}")

        result = authenticate_employee(emp_id, password)
        print(f"Auth result: {result}")

        if not result or not result.get('authenticated'):
            flash('Invalid employee ID or password')
            return render_template('login.html', role=role)

        employee = result['employee']
        print(f"Employee data received: {employee}")

        # Case-insensitive role comparison
        if employee['role'].lower().replace(' ', '_') != role.lower():
            flash(f'This employee ID is not registered as a {role.replace("_", " ")}')
            return render_template('login.html', role=role)

        # Store session data
        session.update({
            'emp_id': emp_id,
            'role': employee['role'],
            'name': employee['name'],
            'email': employee['email']
        })

        # Debug print session data
        print(f"\n--- SESSION DATA ---\n{session}\n")

        # Handle first login (using get() with True default)
        first_login = employee.get('is_first_login', True)
        print(f"First login status: {first_login} (Type: {type(first_login)})")

        if first_login:
            print("Redirecting to change_password")
            return redirect(url_for('change_password'))

        # Regular redirect based on role
        print(f"Redirecting to {role}_dashboard")
        return redirect(url_for(f'{role}_dashboard'))

    return render_template('login.html', role=role)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'emp_id' not in session:
        return redirect(url_for('index'))
    
    # Add debug logging
    print(f"Reached change_password route for employee {session['emp_id']}")
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('New passwords do not match')
            return render_template('change_password.html')
        
        # Call API to change password
        result = change_employee_password(session['emp_id'], current_password, new_password)
        
        if not result or not result.get('success'):
            flash('Current password is incorrect')
            return render_template('change_password.html')
        
        flash('Password changed successfully')
        
        # Redirect based on role
        role = session['role'].lower().replace(' ', '_')
        if role == 'developer':
            return redirect(url_for('developer_dashboard'))
        elif role == 'project_manager':
            return redirect(url_for('project_manager_dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('hr_dashboard'))
    
    # Get employee to check first_login status
    employee = get_employee(session['emp_id'])
    first_login = employee['is_first_login'] if employee else False
    
    print(f"Employee first_login status: {first_login}")
    
    return render_template('change_password.html', first_login=first_login)

@app.route('/developer_dashboard')
def developer_dashboard():
    if 'emp_id' not in session:
        flash('Please log in to access the developer dashboard', 'warning')
        return redirect(url_for('login'))
    
    normalized_role = session.get('role', '').lower().replace(' ', '_')
    if normalized_role != 'developer':
        flash('Access restricted to developers only', 'danger')
        return redirect(url_for('index'))
    
    # Fetch complete employee data
    employee_data = get_employee(session['emp_id'])
    
    # Fallback with defaults if needed
    if not employee_data:
        employee_data = dict(session)
        employee_data['success_rate'] = 0.0
        employee_data['tasks_completed'] = 0
        employee_data['experience'] = 0
        employee_data['skills'] = []
    
    # Get assigned tasks for this developer
    assigned_tasks = get_developer_tasks(session['emp_id'])
    
    # Calculate dashboard statistics from local data
    dashboard_data = calculate_dashboard_metrics(assigned_tasks, employee_data)
    
    # Categorize tasks by status - Updated to match Task model status values
    in_progress_tasks = [task for task in assigned_tasks if task.get('status') == 'in_progress']
    pending_tasks = [task for task in assigned_tasks if task.get('status') == 'assigned']
    pending_approval_tasks = [task for task in assigned_tasks if task.get('status') == 'submitted']
    completed_tasks = [task for task in assigned_tasks if task.get('status') == 'completed']
    
    # Calculate performance history (last 6 months)
    performance_history = get_performance_history(session['emp_id'])
    
    # Get project types from local function
    project_types, _ = get_project_types()
    
    # Get notification count for this developer
    notification_count = get_notification_count(session['emp_id'])
    
    return render_template(
        'developer_dashboard.html', 
        employee=employee_data,
        tasks=assigned_tasks,
        in_progress_tasks=in_progress_tasks,
        pending_tasks=pending_tasks,
        pending_approval_tasks=pending_approval_tasks,  # Updated variable name
        completed_tasks=completed_tasks,
        dashboard=dashboard_data,
        performance_history=performance_history,
        project_types=project_types,
        notification_count=notification_count,
        format_date=format_date,
        faq_items=get_faq_content('developer')
    )


def get_notification_count(emp_id):
    """Get notification count for developer (new tasks, status changes, etc.)"""
    try:
        # Count notifications based on:
        # 1. New tasks assigned (status = 'assigned')
        # 2. Tasks that need attention (overdue, rejected, etc.)
        # 3. Recent task updates
        
        # For now, count assigned tasks + tasks submitted for approval as active notifications
        assigned_count = Task.query.filter_by(assigned_to=emp_id, status='assigned').count()
        submitted_count = Task.query.filter_by(assigned_to=emp_id, status='submitted').count()
        
        # You could also add more sophisticated notification logic here
        # For example: tasks with approaching due dates, feedback received, etc.
        
        total_notifications = assigned_count + submitted_count
        return total_notifications
        
    except Exception as e:
        print(f"Error getting notification count for {emp_id}: {str(e)}")
        return 0

def calculate_dashboard_metrics(tasks, employee_data):
    """Calculate dashboard metrics when API doesn't return data"""
    dashboard = {
        'success_rate': 0.0,
        'tasks_completed': 0,
        'avg_completion_time': 0,
        'performance_trend': []
    }
    
    # Count completed tasks
    completed_tasks = [task for task in tasks if task.get('status') == 'completed']
    dashboard['tasks_completed'] = len(completed_tasks)
    
    # Calculate success rate
    if dashboard['tasks_completed'] > 0:
        # Get average of task ratings
        ratings = [task.get('success_rating', 0) for task in completed_tasks if task.get('success_rating') is not None]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            # Convert 5-star rating to percentage (e.g., 4/5 = 80%)
            dashboard['success_rate'] = (avg_rating / 5) * 100
        else:
            # Default to 70% if no ratings available
            dashboard['success_rate'] = 70.0
    else:
        # No completed tasks yet, use N/A or default value
        dashboard['success_rate'] = employee_data.get('success_rate', 0.0)
    
    # Calculate average completion time (in days)
    if completed_tasks:
        completion_times = []
        for task in completed_tasks:
            start_date = parse_date(task.get('start_date'))
            completion_date = parse_date(task.get('completion_date'))
            if start_date and completion_date:
                delta = completion_date - start_date
                completion_times.append(delta.days)
        
        if completion_times:
            dashboard['avg_completion_time'] = sum(completion_times) / len(completion_times)
    
    return dashboard

def get_performance_history(emp_id, months=6):
    """Get the performance history for the last X months from local database"""
    today = datetime.now()
    
    # Default data structure with empty values
    history = {
        'labels': [],
        'success_rates': []
    }
    
    try:
        # Get employee data for current success rate
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        current_success_rate = employee.success_rate if employee else 75.0
        
        # Get tasks for this employee to calculate actual history
        tasks = Task.query.filter_by(assigned_to=emp_id).all()
        
        # If we have actual task data, use it for more recent months
        if tasks:
            # Calculate historical performance based on actual task completions
            for i in range(months, 0, -1):
                month_date = today - timedelta(days=30*i)
                month_name = month_date.strftime('%b')
                history['labels'].append(month_name)
                
                # Calculate performance for this month based on tasks
                month_start = month_date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_tasks = [t for t in tasks if t.completion_date and 
                             month_start <= t.completion_date <= month_end]
                
                if month_tasks:
                    # Calculate actual success rate for this month
                    completed_tasks = [t for t in month_tasks if t.status == 'completed']
                    success_rate = (len(completed_tasks) / len(month_tasks)) * 100
                else:
                    # Use trending data based on current success rate
                    # Show gradual improvement over time
                    trend_factor = (months - i) / months  # 0 to 1
                    base_rate = max(current_success_rate - 20, 50)  # Start lower
                    success_rate = base_rate + (trend_factor * (current_success_rate - base_rate))
                    success_rate = min(success_rate + random.randint(-5, 3), 95)
                
                history['success_rates'].append(round(success_rate, 1))
        else:
            # Generate sample data that trends toward current success rate
            for i in range(months, 0, -1):
                month_date = today - timedelta(days=30*i)
                month_name = month_date.strftime('%b')
                history['labels'].append(month_name)
                
                # Show improvement trend toward current rate
                progress = (months - i) / months
                start_rate = max(current_success_rate - 25, 50)
                rate = start_rate + (progress * (current_success_rate - start_rate))
                rate = min(rate + random.randint(-3, 5), 95)
                history['success_rates'].append(round(rate, 1))
    
    except Exception as e:
        print(f"Error calculating performance history: {str(e)}")
        # Fallback to simple sample data
        for i in range(months, 0, -1):
            month_date = today - timedelta(days=30*i)
            month_name = month_date.strftime('%b')
            history['labels'].append(month_name)
            
            base_rate = 70 + (i * 2)
            rate = min(base_rate + random.randint(-3, 5), 95)
            history['success_rates'].append(rate)
    
    return history

def parse_date(date_str):
    """Parse date string to datetime object"""
    if not date_str:
        return None
    
    try:
        # Adjust the format based on your date string format
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            # Try another common format
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return None

@app.route('/api/assign_multiple_employees', methods=['POST'])
def assign_multiple_employees():
    if 'emp_id' not in session or session['role'] != 'project manager':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    task_id = request.json.get('task_id')
    employee_ids = request.json.get('employee_ids', [])
    
    if not task_id or not employee_ids:
        return jsonify({'success': False, 'error': 'Task ID and at least one employee ID are required'}), 400
    
    try:
        # Call the task service API to assign multiple employees to the task
        response = requests.post(
            f'{request.host_url.rstrip("/")}/api/task-service/tasks/{task_id}/assign',
            headers=api_headers(),
            json={
                'manager_id': session['emp_id'],
                'employee_ids': employee_ids
            }
        )
        
        if response.status_code != 200:
            return jsonify({'success': False, 'error': f'Failed to assign employees: {response.text}'}), 500
        
        result = response.json()
        return jsonify({'success': True, 'assignments': result.get('assignments', {})})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/project_manager_dashboard')
def project_manager_dashboard():
    if 'emp_id' not in session or session['role'] != 'project manager':
        return redirect(url_for('index'))
    
    # Fetch complete employee data from the employee service
    employee_data = get_employee(session['emp_id'])
    
    # If employee data couldn't be fetched, use session data as fallback with defaults
    if not employee_data:
        employee_data = dict(session)
        employee_data['success_rate'] = 0.0
        employee_data['tasks_completed'] = 0
        employee_data['experience'] = 0
    
    # Get all employees for team stats
    all_employees = get_all_employees()
    
    # Get active tasks count from local database
    active_tasks_count = Task.query.filter(Task.status.in_(['assigned', 'in_progress'])).count()
    
    # Calculate team statistics
    team_stats = {
        'total_members': len(all_employees),
        'active_tasks': active_tasks_count,
        'avg_success': sum(emp.get('success_rate', 0) for emp in all_employees) / len(all_employees) if all_employees else 0,
        'top_skills': {},
        'top_performers': sorted(
            [emp for emp in all_employees if emp.get('tasks_completed', 0) > 0],
            key=lambda x: x.get('success_rate', 0),
            reverse=True
        )[:3]  # Top 3 performers
    }
    
    # Calculate skill distribution
    skill_counts = {}
    for emp in all_employees:
        for skill in emp.get('skills', []):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    team_stats['top_skills'] = dict(sorted(skill_counts.items(), key=lambda item: item[1], reverse=True)[:5])  # Top 5 skills
    
    # Get project types from task service
    project_types, project_type_details = get_project_types()
    
    # Get pending tasks (submitted tasks waiting for approval)
    pending_tasks = get_pending_tasks()
    
    return render_template(
        'project_manager_dashboard.html',
        employee=employee_data,
        team_stats=team_stats,
        project_types=project_types,
        project_type_details=project_type_details,
        pending_tasks=pending_tasks,
        faq_items=get_faq_content('project manager')
    )


@app.route('/task_management')
def task_management():
    if 'emp_id' not in session or session['role'] != 'project manager':
        flash('Access restricted to project managers', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters from query string
    status_filter = request.args.get('status', 'all')
    project_type_filter = request.args.get('project_type', 'all')
    assignee_filter = request.args.get('assignee', 'all')
    
    # Get project types and their details
    project_types, project_type_details = get_project_types()
    
    # Get all employees for assignment dropdown
    employees = get_all_employees()
    
    try:
        # Get all tasks from local database
        query = Task.query
        
        # Apply filters
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)
        if project_type_filter != 'all':
            query = query.filter_by(project_type=project_type_filter)
        if assignee_filter != 'all':
            query = query.filter_by(assigned_to=assignee_filter)
        
        tasks_from_db = query.all()
        
        # Convert to list of dictionaries
        tasks = []
        for task in tasks_from_db:
            # Get employee info
            employee = Employee.query.filter_by(emp_id=task.assigned_to).first()
            
            task_dict = {
                'task_id': task.task_id,
                'title': task.title,
                'description': task.description,
                'project_type': task.project_type,
                'complexity': task.complexity,
                'priority': task.priority,
                'status': task.status,
                'assigned_to': task.assigned_to,
                'assigned_to_name': employee.name if employee else 'Unknown',
                'assigned_at': task.assigned_at.isoformat() if task.assigned_at else None,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'submitted_at': task.submitted_at.isoformat() if task.submitted_at else None,
                'completion_date': task.completion_date.isoformat() if task.completion_date else None
            }
            tasks.append(task_dict)
        
        # Categorize tasks by status for easier display
        pending_review_tasks = [task for task in tasks if task.get('status') == 'submitted']
        assigned_tasks = [task for task in tasks if task.get('status') == 'assigned']
        in_progress_tasks = [task for task in tasks if task.get('status') == 'in_progress']
        completed_tasks = [task for task in tasks if task.get('status') == 'completed']
        
        return render_template(
            'task_management.html',
            project_types=project_types,
            project_type_details=project_type_details,
            employees=employees,
            tasks=tasks,
            pending_review_tasks=pending_review_tasks,
            assigned_tasks=assigned_tasks,
            in_progress_tasks=in_progress_tasks,
            completed_tasks=completed_tasks,
            status_filter=status_filter,
            project_type_filter=project_type_filter,
            assignee_filter=assignee_filter,
            format_date=format_date
        )
    
    except Exception as e:
        flash(f'Error fetching task data: {str(e)}', 'danger')
        return render_template(
            'task_management.html',
            project_types=project_types,
            project_type_details=project_type_details,
            employees=employees,
            tasks=[],
            pending_review_tasks=[],
            assigned_tasks=[],
            in_progress_tasks=[],
            completed_tasks=[]
        )

@app.route('/approve_task', methods=['POST'])
def approve_task():
    """Approve or reject a submitted task using local database"""
    if 'emp_id' not in session or session['role'] != 'project manager':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    task_id = request.json.get('task_id')
    action = request.json.get('action')  # 'approve' or 'reject'
    feedback = request.json.get('feedback', '')
    
    if not task_id or not action:
        return jsonify({'success': False, 'error': 'Task ID and action are required'}), 400
    
    if action not in ['approve', 'reject']:
        return jsonify({'success': False, 'error': 'Invalid action'}), 400
    
    try:
        # Get the task from local database
        task = Task.query.filter_by(task_id=task_id).first()
        if not task:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        
        # Check if task is in submitted status
        if task.status != 'submitted':
            return jsonify({'success': False, 'error': f'Cannot review task with status: {task.status}. Task must be submitted.'}), 400
        
        # Update task based on action
        if action == 'approve':
            task.status = 'completed'
            task.completion_date = datetime.utcnow()
            task.success_rating = 5  # Default rating for approved tasks
            
            # Update employee success rate
            employee = Employee.query.filter_by(emp_id=task.assigned_to).first()
            if employee:
                employee.tasks_completed = (employee.tasks_completed or 0) + 1
                # Calculate new success rate (simple approach)
                total_tasks = employee.tasks_completed
                current_successful = int((employee.success_rate or 0) / 100 * (total_tasks - 1))
                new_success_rate = ((current_successful + 1) / total_tasks) * 100
                employee.success_rate = min(new_success_rate, 100.0)
        else:  # reject
            task.status = 'assigned'  # Send back for rework
            task.completion_date = None
            task.submitted_at = None
            task.success_rating = None
        
        # Add feedback
        if feedback:
            task.feedback = feedback
        
        # Update timestamp
        task.updated_at = datetime.utcnow()
        
        # Commit changes
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Task {action}ed successfully',
            'task': task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in approve_task: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to {action} task: {str(e)}'}), 500






@app.route('/hr_dashboard')
def hr_dashboard():
    if 'emp_id' not in session or session['role'] != 'human resource':
        return redirect(url_for('index'))
    return render_template('hr_dashboard.html', employee=session)

@app.route('/admin/create_employee', methods=['GET', 'POST'])
def create_employee():
    if 'emp_id' not in session or session['role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Employee ID is now optional
        emp_id = request.form.get('emp_id', '').strip()
        name = request.form.get('name')
        email = request.form.get('email')
        role = request.form.get('role')
        
        # Get skills as a list from the comma-separated input
        skills_input = request.form.get('skills', '').strip()
        skills = [skill.strip() for skill in skills_input.split(',')] if skills_input else None
        
        # Get experience as an integer
        experience_input = request.form.get('experience', '').strip()
        experience = int(experience_input) if experience_input and experience_input.isdigit() else None
        
        # Call API to create employee with the new parameters
        success, result = create_new_employee(
            name=name,
            email=email,
            role=role,
            skills=skills,
            experience=experience,
            emp_id=emp_id if emp_id else None
        )
        
        if not success:
            flash(f'Failed to create employee: {result}')
        else:
            # Get the assigned employee ID for the success message
            assigned_emp_id = result if isinstance(result, str) else emp_id
            flash(f'Employee created with ID: {assigned_emp_id}. Credentials sent via email.')
        
        return redirect(url_for('admin_dashboard'))
    
    # Get project types for skill suggestions
    project_types, project_type_details = get_project_types()
    all_skills = []
    for skills_list in project_type_details.values():
        all_skills.extend(skills_list)
    # Remove duplicates while preserving order
    unique_skills = list(dict.fromkeys(all_skills))
    
    return render_template('create_employee.html', skills=unique_skills)

@app.route('/admin/edit_employee/<emp_id>', methods=['GET', 'POST'])
def edit_employee(emp_id):
    if 'emp_id' not in session or session['role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('index'))
    
    employee = get_employee(emp_id)
    if not employee:
        flash('Employee not found')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'role': request.form.get('role')
        }
        
        # Update employee via API
        result = update_employee(emp_id, data)
        
        if not result:
            flash('Failed to update employee')
            return render_template('edit_employee.html', employee=employee)
        
        flash('Employee updated successfully')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_employee.html', employee=employee)

@app.route('/admin/delete_employee/<emp_id>', methods=['POST'])
def admin_delete_employee(emp_id):
    if 'emp_id' not in session or session['role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('index'))
    
    if emp_id == session['emp_id']:
        flash('Cannot delete your own account')
        return redirect(url_for('admin_dashboard'))
    
    # Delete employee via API
    if delete_employee(emp_id):
        flash('Employee deleted successfully')
    else:
        flash('Failed to delete employee')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'emp_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    # Get all employees from API
    employees = get_all_employees()
    
    return render_template('admin_dashboard.html', employees=employees, current_user=session, faq_items=get_faq_content('admin'))
@app.route('/admin/update_metrics/<emp_id>', methods=['POST'])
def update_metrics(emp_id):
    if 'emp_id' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Prepare update data
    update_data = {}
    if 'tasks_completed' in data:
        update_data['tasks_completed'] = data['tasks_completed']
    if 'success_rate' in data:
        update_data['success_rate'] = data['success_rate']
    
    # Update employee via API
    result = update_employee(emp_id, update_data)
    
    if not result:
        return jsonify({'success': False, 'error': 'Failed to update employee metrics'}), 500
    
    return jsonify({'success': True})


@app.route('/api/create_task', methods=['POST'])
def create_task():
    """Create a new task and assign to employee with optional file upload"""
    if 'emp_id' not in session or session.get('role') != 'project manager':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        # Handle multipart form data (for file upload)
        if request.content_type and 'multipart/form-data' in request.content_type:
            task_data = request.form.to_dict()
            # Convert skills from string to list if present
            if 'skills' in task_data:
                import json
                try:
                    task_data['skills'] = json.loads(task_data['skills'])
                except:
                    task_data['skills'] = []
        else:
            task_data = request.json or {}
        
        # Validate task data
        required_fields = ['task_id', 'project_type', 'complexity', 'priority']
        for field in required_fields:
            if field not in task_data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Get recommendation for best employee
        recommendation = get_task_assignment_recommendation(task_data)
        
        if not recommendation:
            return jsonify({'success': False, 'error': 'No suitable employee found for this task'}), 400
        
        # Handle REQUIRED ZIP file upload
        spec_zip_path = None
        spec_original_name = None
        spec_size_bytes = None
        spec_uploaded_at = None
        
        # Check if request has files at all (multipart form data)
        if not request.files or 'spec_file' not in request.files:
            return jsonify({'success': False, 'error': 'Specification ZIP file is required'}), 400
            
        file = request.files['spec_file']
        if not file or not file.filename:
            return jsonify({'success': False, 'error': 'Specification ZIP file is required'}), 400
            
        try:
            spec_zip_path, spec_original_name, spec_size_bytes = save_spec_file(file, task_data['task_id'])
            spec_uploaded_at = datetime.utcnow()
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': 'Failed to save specification file'}), 500
        
        # Create new task in database
        new_task = Task(
            task_id=task_data['task_id'],
            title=task_data.get('title', f"{task_data['project_type'].replace('_', ' ').title()} Task"),
            description=task_data.get('description', f"New {task_data['project_type']} task"),
            project_type=task_data['project_type'],
            complexity=task_data['complexity'],
            priority=task_data['priority'],
            status='assigned',
            assigned_to=recommendation['emp_id'],
            assigned_by=session['emp_id'],
            due_date=datetime.utcnow() + timedelta(days=7),  # Default 7 days
            spec_zip_path=spec_zip_path,
            spec_original_name=spec_original_name,
            spec_size_bytes=spec_size_bytes,
            spec_uploaded_at=spec_uploaded_at
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'task': {
                'task_id': new_task.task_id,
                'title': new_task.title,
                'project_type': new_task.project_type,
                'assigned_to': new_task.assigned_to,
                'has_spec_file': spec_zip_path is not None,
                'spec_file_name': spec_original_name,
                'spec_file_size': spec_size_bytes
            },
            'assignment': {
                'emp_id': recommendation['emp_id'],
                'name': recommendation['name'],
                'match_score': recommendation.get('match_score', 'N/A')
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating task: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/submit_task_for_review', methods=['POST'])
def submit_task_for_review():
    """Submit a task for review using local database"""
    if 'emp_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({'success': False, 'error': 'Task ID required'}), 400

        # Find task in local database
        task = Task.query.filter_by(task_id=task_id).first()
        
        if not task:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        
        # Check if user is assigned to this task
        if task.assigned_to != session['emp_id']:
            return jsonify({'success': False, 'error': 'You can only submit tasks assigned to you'}), 403
        
        # Update task status to submitted
        task.status = 'submitted'
        task.submitted_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Task {task_id} submitted for review',
            'task': {
                'task_id': task.task_id,
                'status': task.status,
                'submitted_at': task.submitted_at.isoformat() if task.submitted_at else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting task for review: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_task/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get details for a specific task from local database"""
    if 'emp_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Get task from local database
        task = Task.query.filter_by(task_id=task_id).first()
        if not task:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        
        # Get employee who submitted the task
        employee = Employee.query.filter_by(emp_id=task.assigned_to).first()
        
        # Format task data
        task_data = {
            'task_id': task.task_id,
            'title': task.title,
            'description': task.description,
            'project_type': task.project_type,
            'complexity': task.complexity,
            'priority': task.priority,
            'status': task.status,
            'assigned_to': task.assigned_to,
            'assigned_by': task.assigned_by,
            'submitted_by_name': employee.name if employee else 'Unknown',
            'submitted_by_id': task.assigned_to,
            'submitted_at': task.submitted_at.isoformat() if task.submitted_at else None,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'success_rating': task.success_rating,
            'feedback': task.feedback
        }
        
        return jsonify({'success': True, 'task': task_data})
    
    except Exception as e:
        app.logger.error(f"Error getting task {task_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/pending_review_tasks', methods=['GET'])
def get_pending_review_tasks():
    """Get tasks that are submitted and waiting for project manager review"""
    if 'emp_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Only allow project managers to access this
    if session.get('role') != 'project manager':
        return jsonify({'success': False, 'error': 'Access restricted to project managers'}), 403
    
    try:
        # Get tasks with 'submitted' status from local database
        submitted_tasks = Task.query.filter_by(status='submitted').all()
        
        # Convert to list of dictionaries with employee info
        tasks_data = []
        for task in submitted_tasks:
            # Get employee who submitted the task
            employee = Employee.query.filter_by(emp_id=task.assigned_to).first()
            
            task_dict = {
                'task_id': task.task_id,
                'title': task.title,
                'description': task.description,
                'project_type': task.project_type,
                'complexity': task.complexity,
                'priority': task.priority,
                'status': task.status,
                'assigned_to': task.assigned_to,
                'assigned_to_name': employee.name if employee else 'Unknown',
                'assigned_by': task.assigned_by,
                'submitted_at': task.submitted_at.isoformat() if task.submitted_at else None,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'created_at': task.created_at.isoformat() if task.created_at else None
            }
            tasks_data.append(task_dict)
        
        return jsonify({
            'success': True,
            'tasks': tasks_data,
            'count': len(tasks_data)
        })
    
    except Exception as e:
        print(f"Error getting pending review tasks: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get pending tasks: {str(e)}'
        }), 500

@app.route('/task_details/<task_id>')
def task_details(task_id):
    if 'emp_id' not in session:
        flash('Please log in to view task details', 'warning')
        return redirect(url_for('login'))
    
    try:
        # Get task from local database
        task = Task.query.filter_by(task_id=task_id).first()
        
        if not task:
            flash('Task not found', 'danger')
            return redirect(url_for('index'))
        
        # Get assigned employee details
        assignee = None
        if task.assigned_to:
            assignee = Employee.query.filter_by(emp_id=task.assigned_to).first()
        
        # Get task submission if exists
        submission = TaskSubmission.query.filter_by(task_id=task_id).first()
        
        # Convert task to dict format for template compatibility
        task_dict = {
            'task_id': task.task_id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'project_type': task.project_type,
            'complexity': task.complexity,
            'estimated_hours': task.estimated_hours,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'assigned_to': task.assigned_to,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'updated_at': task.updated_at.isoformat() if task.updated_at else None,
            'spec_zip_path': task.spec_zip_path,
            'spec_original_name': task.spec_original_name,
            'spec_size_bytes': task.spec_size_bytes,
            'spec_uploaded_at': task.spec_uploaded_at.isoformat() if task.spec_uploaded_at else None
        }
        
        # Convert assignee to dict if exists
        assignee_dict = None
        if assignee:
            assignee_dict = {
                'emp_id': assignee.emp_id,
                'name': assignee.name,
                'email': assignee.email,
                'role': assignee.role,
                'experience': assignee.experience,
                'skills': assignee.get_skills_list()
            }
        
        # Convert submission to dict if exists
        submission_dict = None
        if submission:
            submission_dict = {
                'id': submission.id,
                'task_id': submission.task_id,
                'developer_id': submission.developer_id,
                'submit_zip_path': submission.submit_zip_path,
                'submit_original_name': submission.submit_original_name,
                'submit_size_bytes': submission.submit_size_bytes,
                'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                'notes': submission.notes
            }
        
        # Different templates based on user role
        if session.get('role') == 'project_manager':
            return render_template(
                'task_details.html',
                task=task_dict,
                assignee=assignee_dict,
                submission=submission_dict,
                is_pm=True,
                format_date=format_date
            )
        else:
            # Check if current user is assigned to this task
            is_assigned = (task.assigned_to == session.get('emp_id'))
            
            return render_template(
                'task_details.html',
                task=task_dict,
                assignee=assignee_dict,
                submission=submission_dict,
                is_assigned=is_assigned,
                is_pm=False,
                format_date=format_date
            )
    
    except Exception as e:
        flash(f'Error retrieving task details: {str(e)}', 'danger')
        return redirect(url_for('index'))


@app.route('/api/get_assignment_recommendation', methods=['POST'])
def get_assignment_recommendation():
    """Get assignment recommendation for a task without saving it"""
    if 'emp_id' not in session or session.get('role') != 'project manager':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    task_data = request.json
    tasks = [task_data]
    
    # Get skills for project type if not provided
    if 'skills' not in task_data or not task_data['skills']:
        task_data['skills'] = get_skills_for_project_type(task_data['project_type'])
    
    # Get recommendation using local function
    try:
        recommendation = get_task_assignment_recommendation(task_data)
        
        if recommendation:
            return jsonify({
                'success': True,
                'recommendations': recommendation
            })
        else:
            return jsonify({
                'success': False,
                'recommendations': 'No suitable employee found'
            })
    except Exception as e:
        import traceback
        print(f"Error in get_assignment_recommendation: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Exception: {str(e)}'
        }), 500



@app.route('/update_task_status', methods=['POST'])
def update_task_status():
    """Update a task's status using local database"""
    if 'emp_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
    try:
        data = request.json
        if not data or 'task_id' not in data or 'status' not in data:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        task_id = data['task_id']
        if not task_id:
            return jsonify({'success': False, 'error': 'Invalid task ID'}), 400
            
        new_status = data['status']
        emp_id = session['emp_id']
        
        # Find the task in local database
        task = Task.query.filter_by(task_id=task_id).first()
        
        if not task:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        
        # Check if user can update this task (must be assigned to them or be a manager)
        if task.assigned_to != emp_id and session.get('role') not in ['project manager', 'admin']:
            return jsonify({'success': False, 'error': 'Unauthorized to update this task'}), 403
        
        # Update task status
        task.status = new_status
        task.updated_at = datetime.utcnow()
        
        # Update specific timestamp fields based on status
        if new_status == 'in_progress':
            task.start_date = datetime.utcnow()
        elif new_status == 'submitted':
            task.submitted_at = datetime.utcnow()
        elif new_status == 'completed':
            task.completion_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Task {task_id} status updated to {new_status}',
            'task': {
                'task_id': task.task_id,
                'status': task.status,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating task status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Modified get_all_tasks function to ensure Task is defined
@app.route('/api/task-service/tasks', methods=['GET'])
def get_all_tasks():
    """Get all tasks or filter by employee, status, etc."""
    try:
        # Get query parameters for filtering
        emp_id = request.args.get('emp_id')
        status = request.args.get('status')
        project_type = request.args.get('project_type')
        
        # Start with base query - make sure Task is defined in this scope
        query = Task.query
        
        # Apply filters if provided
        if emp_id:
            query = query.filter_by(assigned_to=emp_id)
        if status:
            query = query.filter_by(status=status)
        if project_type:
            query = query.filter_by(project_type=project_type)
            
        # Execute query and convert to dict
        tasks = query.all()
        task_list = [task.to_dict() for task in tasks]
        
        return jsonify({
            'success': True,
            'tasks': task_list,
            'count': len(task_list)
        })
    except Exception as e:
        print(f"Error getting tasks: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add a jinja template filter for formatting dates
@app.template_filter('datetime')
def format_datetime(value, format='%B %d, %Y %I:%M %p'):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    return value.strftime(format)

@app.route('/download_task_file/<task_id>')
def download_task_file(task_id):
    """Download task file (for developers)"""
    if 'emp_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Check if user is authorized to download this file
    task = Task.query.filter_by(task_id=task_id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Developers can download files for their assigned tasks
    # Project managers can download any task file
    if session.get('role') not in ['developer', 'project manager']:
        return jsonify({'error': 'Access denied'}), 403
    
    if session.get('role') == 'developer' and task.assigned_to != session['emp_id']:
        return jsonify({'error': 'Access denied - task not assigned to you'}), 403
    
    if not task.task_file_path or not os.path.exists(task.task_file_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        from flask import send_file
        return send_file(
            task.task_file_path,
            as_attachment=True,
            download_name=task.task_file_name or f"{task_id}_task.zip",
            mimetype='application/zip'
        )
    except Exception as e:
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@app.route('/download_submission_file/<task_id>')
def download_submission_file(task_id):
    """Download submission file (for project managers)"""
    if 'emp_id' not in session or session.get('role') != 'project manager':
        return jsonify({'error': 'Unauthorized'}), 401
    
    task = Task.query.filter_by(task_id=task_id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if not task.submission_file_path or not os.path.exists(task.submission_file_path):
        return jsonify({'error': 'Submission file not found'}), 404
    
    try:
        from flask import send_file
        return send_file(
            task.submission_file_path,
            as_attachment=True,
            download_name=task.submission_file_name or f"{task_id}_submission.zip",
            mimetype='application/zip'
        )
    except Exception as e:
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@app.route('/download_spec_file/<task_id>')
def download_spec_file(task_id):
    """Download specification ZIP file with secure access control"""
    if 'emp_id' not in session:
        return jsonify({'error': 'Unauthorized - Please login'}), 401
    
    # Get the task from database
    task = Task.query.filter_by(task_id=task_id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Authorization checks:
    # - Developers can download spec files for their assigned tasks
    # - Project managers can download any spec file
    # - Admins can download any spec file
    user_role = session.get('role')
    user_emp_id = session.get('emp_id')
    
    if user_role == 'developer':
        if task.assigned_to != user_emp_id:
            return jsonify({'error': 'Access denied - task not assigned to you'}), 403
    elif user_role not in ['project manager', 'admin']:
        return jsonify({'error': 'Access denied - insufficient permissions'}), 403
    
    # Check if spec file exists
    if not task.spec_zip_path:
        return jsonify({'error': 'No specification file uploaded for this task'}), 404
    
    # Check if file exists on filesystem
    if not os.path.exists(task.spec_zip_path):
        return jsonify({'error': 'Specification file not found on server'}), 404
    
    try:
        # Serve file securely with original filename
        return send_file(
            task.spec_zip_path,
            as_attachment=True,
            download_name=task.spec_original_name or f"{task_id}_spec.zip",
            mimetype='application/zip'
        )
    except Exception as e:
        print(f"Error downloading spec file for task {task_id}: {str(e)}")
        return jsonify({'error': 'Error downloading specification file'}), 500

@app.route('/tasks/<task_id>/download-spec')
def download_task_spec(task_id):
    """Secure download route for task specifications with authorization and path traversal protection"""
    # Authentication check
    if 'emp_id' not in session:
        flash('Please log in to download task specifications', 'warning')
        return redirect(url_for('login'))
    
    try:
        # Get the task from database
        task = Task.query.filter_by(task_id=task_id).first()
        if not task:
            flash('Task not found', 'error')
            return redirect(url_for('developer_dashboard'))
        
        # Authorization checks:
        # - Developers can only download specs for their assigned tasks
        # - Project managers can download any task spec
        # - Admins can download any task spec
        user_role = session.get('role')
        user_emp_id = session.get('emp_id')
        
        if user_role == 'developer':
            if task.assigned_to != user_emp_id:
                flash('Access denied - task not assigned to you', 'error')
                return redirect(url_for('developer_dashboard'))
        elif user_role not in ['project manager', 'admin']:
            flash('Access denied - insufficient permissions', 'error')
            return redirect(url_for('developer_dashboard'))
        
        # Check if spec file exists in database
        if not task.spec_zip_path:
            flash('No specification file available for this task', 'info')
            return redirect(url_for('developer_dashboard'))
        
        # Validate and secure the file path to prevent path traversal
        # The spec_zip_path should be relative to the app root
        try:
            # Normalize the path and ensure it's within the upload directory
            upload_root = os.path.abspath(app.config['UPLOAD_FOLDER'])
            file_path = os.path.abspath(task.spec_zip_path)
            
            # Security check: ensure file is within upload directory
            if not file_path.startswith(upload_root):
                flash('Invalid file path', 'error')
                return redirect(url_for('developer_dashboard'))
            
            # Check if file exists on filesystem
            if not os.path.exists(file_path):
                flash(f'Specification file not found on server. Please contact support.', 'error')
                return redirect(url_for('developer_dashboard'))
            
            # Use send_from_directory for secure file serving
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            
            return send_from_directory(
                directory, 
                filename,
                as_attachment=True,
                download_name=task.spec_original_name or f"{task_id}_spec.zip",
                mimetype='application/zip'
            )
            
        except Exception as file_error:
            print(f"File system error for task {task_id}: {str(file_error)}")
            flash('Error accessing specification file', 'error')
            return redirect(url_for('developer_dashboard'))
    
    except Exception as e:
        print(f"Error in download_task_spec for task {task_id}: {str(e)}")
        flash('An error occurred while downloading the file', 'error')
        return redirect(url_for('developer_dashboard'))

@app.route('/tasks/<task_id>/submit', methods=['POST'])
def submit_task_with_file(task_id):
    """Developer submits task with ZIP file and optional notes"""
    # Authentication check
    if 'emp_id' not in session or session.get('role') != 'developer':
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    
    try:
        # Get the task from database
        task = Task.query.filter_by(task_id=task_id).first()
        if not task:
            flash('Task not found', 'error')
            return redirect(url_for('developer_dashboard'))
        
        # Authorization check: Only assigned developer can submit
        if task.assigned_to != session['emp_id']:
            flash('You can only submit tasks assigned to you', 'error')
            return redirect(url_for('developer_dashboard'))
        
        # Check if task is in submittable state
        if task.status != 'in_progress':
            flash(f'Cannot submit task with status: {task.status}. Task must be in progress to submit.', 'error')
            return redirect(url_for('developer_dashboard'))
        
        # Validate required file upload
        if 'submission_file' not in request.files:
            flash('Submission file is required', 'error')
            return redirect(url_for('task_details', task_id=task_id))
        
        file = request.files['submission_file']
        if not file or not file.filename:
            flash('Please select a ZIP file to submit', 'error')
            return redirect(url_for('task_details', task_id=task_id))
        
        # Get optional notes
        notes = request.form.get('notes', '').strip() or None
        
        # Save submission file
        try:
            submit_zip_path, submit_original_name, submit_size_bytes = save_submission_file(file, task_id)
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('task_details', task_id=task_id))
        except Exception as e:
            flash('Failed to save submission file', 'error')
            return redirect(url_for('task_details', task_id=task_id))
        
        # Check if submission already exists (replace if so)
        existing_submission = TaskSubmission.query.filter_by(task_id=task_id).first()
        
        if existing_submission:
            # Remove old file if it exists
            if existing_submission.submit_zip_path and os.path.exists(existing_submission.submit_zip_path):
                try:
                    os.remove(existing_submission.submit_zip_path)
                except:
                    pass  # Don't fail if old file can't be removed
            
            # Update existing submission
            existing_submission.developer_id = session['emp_id']
            existing_submission.submit_zip_path = submit_zip_path
            existing_submission.submit_original_name = submit_original_name
            existing_submission.submit_size_bytes = submit_size_bytes
            existing_submission.submitted_at = datetime.utcnow()
            existing_submission.notes = notes
        else:
            # Create new submission record
            new_submission = TaskSubmission(
                task_id=task_id,
                developer_id=session['emp_id'],
                submit_zip_path=submit_zip_path,
                submit_original_name=submit_original_name,
                submit_size_bytes=submit_size_bytes,
                notes=notes
            )
            db.session.add(new_submission)
        
        # Update task status to 'submitted'
        task.status = 'submitted'
        task.submitted_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Task submitted successfully!', 'success')
        return redirect(url_for('task_details', task_id=task_id))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting task {task_id}: {str(e)}")
        flash('An error occurred while submitting the task', 'error')
        return redirect(url_for('task_details', task_id=task_id))

@app.route('/tasks/<task_id>/submission/download')
def download_task_submission(task_id):
    """Secure download route for task submissions with authorization checks"""
    # Authentication check
    if 'emp_id' not in session:
        flash('Please log in to download submissions', 'warning')
        return redirect(url_for('login'))
    
    try:
        # Get the submission from database
        submission = TaskSubmission.query.filter_by(task_id=task_id).first()
        if not submission:
            flash('No submission found for this task', 'error')
            return redirect(url_for('task_details', task_id=task_id))
        
        # Authorization checks:
        # - Project managers and admins can download any submission
        # - The submitting developer can download their own submission
        user_role = session.get('role')
        user_emp_id = session.get('emp_id')
        
        if user_role in ['project manager', 'admin']:
            # PM and Admin can download any submission
            pass
        elif user_role == 'developer' and submission.developer_id == user_emp_id:
            # Developer can download their own submission
            pass
        else:
            flash('Access denied - you cannot download this submission', 'error')
            return redirect(url_for('task_details', task_id=task_id))
        
        # Validate and secure the file path to prevent path traversal
        try:
            # Normalize the path and ensure it's within the upload directory
            upload_root = os.path.abspath(app.config['UPLOAD_FOLDER'])
            file_path = os.path.abspath(submission.submit_zip_path)
            
            # Security check: ensure file is within upload directory
            if not file_path.startswith(upload_root):
                flash('Invalid file path', 'error')
                return redirect(url_for('task_details', task_id=task_id))
            
            # Check if file exists on filesystem
            if not os.path.exists(file_path):
                flash('Submission file not found on server. Please contact support.', 'error')
                return redirect(url_for('task_details', task_id=task_id))
            
            # Use send_from_directory for secure file serving
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            
            return send_from_directory(
                directory, 
                filename,
                as_attachment=True,
                download_name=submission.submit_original_name,
                mimetype='application/zip'
            )
            
        except Exception as file_error:
            print(f"File system error for submission {submission.id}: {str(file_error)}")
            flash('Error accessing submission file', 'error')
            return redirect(url_for('task_details', task_id=task_id))
    
    except Exception as e:
        print(f"Error in download_task_submission for task {task_id}: {str(e)}")
        flash('An error occurred while downloading the submission', 'error')
        return redirect(url_for('task_details', task_id=task_id))

@app.route('/api/submit_task', methods=['POST'])
def submit_task():
    """Submit task with optional file upload (for developers)"""
    if 'emp_id' not in session or session.get('role') != 'developer':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        task_id = request.form.get('task_id') if request.form else request.json.get('task_id')
        
        if not task_id:
            return jsonify({'success': False, 'error': 'Task ID is required'}), 400
        
        # Get task from database
        task = Task.query.filter_by(task_id=task_id).first()
        if not task:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        
        # Check if task is assigned to current developer
        if task.assigned_to != session['emp_id']:
            return jsonify({'success': False, 'error': 'Task not assigned to you'}), 403
        
        # Check if task is in correct status
        if task.status not in ['assigned', 'in_progress']:
            return jsonify({'success': False, 'error': f'Cannot submit task with status: {task.status}'}), 400
        
        # Handle file upload
        submission_file_path = task.submission_file_path  # Keep existing file if no new one
        submission_file_name = task.submission_file_name
        
        if 'submission_file' in request.files:
            file = request.files['submission_file']
            if file.filename:
                new_path, new_name = save_uploaded_file(file, task_id, 'submission')
                if new_path:
                    # Remove old file if exists
                    if task.submission_file_path and os.path.exists(task.submission_file_path):
                        try:
                            os.remove(task.submission_file_path)
                        except:
                            pass
                    submission_file_path = new_path
                    submission_file_name = new_name
                else:
                    return jsonify({'success': False, 'error': 'Failed to save submission file. Please ensure it is a .zip file.'}), 400
        
        # Update task status and submission details
        task.status = 'submitted'
        task.submitted_at = datetime.utcnow()
        task.submission_file_path = submission_file_path
        task.submission_file_name = submission_file_name
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task submitted successfully',
            'task': {
                'task_id': task.task_id,
                'status': task.status,
                'submitted_at': task.submitted_at.isoformat() if task.submitted_at else None,
                'has_submission_file': submission_file_path is not None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting task: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/test_email')
def test_email():
    test_email = "lolomoakamela@gmail.com"  # Use a real email you can check
    result = send_credentials_email(
        email=test_email,
        emp_id="TEST123",
        temp_password="testpass123"
    )
    return jsonify({"success": result})

@app.route('/my_tasks')
def my_tasks():
    """Show tasks assigned to the current developer"""
    if 'emp_id' not in session or session.get('role') != 'developer':
        flash('Access restricted to developers', 'danger')
        return redirect(url_for('index'))
    
    # Get status filter from query parameters
    status_filter = request.args.get('status', 'all')
    
    # Get tasks assigned to current employee
    query = Task.query.filter_by(assigned_to=session['emp_id'])
    
    # Apply status filter
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    # Convert to list of dictionaries
    task_list = []
    for task in tasks:
        task_dict = {
            'task_id': task.task_id,
            'title': task.title,
            'description': task.description,
            'project_type': task.project_type,
            'complexity': task.complexity,
            'priority': task.priority,
            'status': task.status,
            'assigned_at': task.assigned_at.isoformat() if task.assigned_at else None,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'submitted_at': task.submitted_at.isoformat() if task.submitted_at else None,
            'completion_date': task.completion_date.isoformat() if task.completion_date else None
        }
        task_list.append(task_dict)
    
    return render_template('my_tasks.html', tasks=task_list, status_filter=status_filter, format_date=format_date)

@app.route('/notifications')
def notifications():
    """Show notifications for the current user"""
    if 'emp_id' not in session:
        flash('Please log in to view notifications', 'warning')
        return redirect(url_for('index'))
    
    # Get notifications from the database
    try:
        notifications_list = Notification.query.filter_by(emp_id=session['emp_id']).order_by(Notification.created_at.desc()).limit(20).all()
        
        notifications = []
        for notif in notifications_list:
            notifications.append({
                'id': notif.id,
                'type': notif.type,
                'message': notif.message,
                'task_id': notif.task_id,
                'timestamp': notif.created_at.isoformat() if notif.created_at else None,
                'is_read': notif.is_read
            })
            
        return render_template('notifications.html', notifications=notifications)
        
    except Exception as e:
        print(f"Error loading notifications: {e}")
        # Fallback to old method if notifications table doesn't exist yet
        recent_tasks = Task.query.filter_by(assigned_to=session['emp_id']).order_by(Task.created_at.desc()).limit(10).all()
        
        notifications = []
        for task in recent_tasks:
            if task.status == 'assigned':
                notifications.append({
                    'type': 'task_assigned',
                    'message': f'New task assigned: {task.title}',
                    'task_id': task.task_id,
                    'timestamp': task.assigned_at.isoformat() if task.assigned_at else None
                })
            elif task.status == 'in_progress':
                notifications.append({
                    'type': 'task_started',
                    'message': f'Task in progress: {task.title}',
                    'task_id': task.task_id,
                    'timestamp': task.start_date.isoformat() if task.start_date else None
                })
        
        return render_template('notifications.html', notifications=notifications)

@app.route('/settings')
def settings():
    """Show user settings page"""
    if 'emp_id' not in session:
        flash('Please log in to access settings', 'warning')
        return redirect(url_for('index'))
    
    # Get current employee data
    employee = get_employee(session['emp_id'])
    
    return render_template('settings.html', employee=employee)

@app.route('/api/add_skill', methods=['POST'])
def add_skill():
    """Add a skill to the current employee"""
    if 'emp_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        skill = data.get('skill', '').strip()
        
        if not skill:
            return jsonify({'success': False, 'error': 'Skill name is required'}), 400
        
        # Get current employee
        employee = Employee.query.filter_by(emp_id=session['emp_id']).first()
        if not employee:
            return jsonify({'success': False, 'error': 'Employee not found'}), 404
        
        # Get current skills
        current_skills = employee.get_skills_list()
        
        # Check if skill already exists (case insensitive)
        if skill.lower() in [s.lower() for s in current_skills]:
            return jsonify({'success': False, 'error': 'Skill already exists'}), 400
        
        # Add new skill
        current_skills.append(skill)
        employee.set_skills_list(current_skills)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Skill added successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding skill: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to add skill'}), 500

@app.route('/api/start_task/<task_id>', methods=['POST'])
def start_task(task_id):
    """Start a task (change status from assigned to in_progress)"""
    if 'emp_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        # Get the task
        task = Task.query.filter_by(task_id=task_id).first()
        if not task:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        
        # Check if task is assigned to current user
        if task.assigned_to != session['emp_id']:
            return jsonify({'success': False, 'error': 'Task not assigned to you'}), 403
        
        # Check if task is in correct status
        if task.status != 'assigned':
            return jsonify({'success': False, 'error': f'Cannot start task with status: {task.status}'}), 400
        
        # Update task status
        task.status = 'in_progress'
        task.start_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Task started successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error starting task {task_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to start task'}), 500

@app.route('/api/remove_skill', methods=['POST'])
def remove_skill():
    """Remove a skill from the current employee"""
    if 'emp_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        skill = data.get('skill', '').strip()
        
        if not skill:
            return jsonify({'success': False, 'error': 'Skill name is required'}), 400
        
        # Get current employee
        employee = Employee.query.filter_by(emp_id=session['emp_id']).first()
        if not employee:
            return jsonify({'success': False, 'error': 'Employee not found'}), 404
        
        # Get current skills
        current_skills = employee.get_skills_list()
        
        # Remove the skill (case insensitive)
        updated_skills = [s for s in current_skills if s.lower() != skill.lower()]
        
        if len(updated_skills) == len(current_skills):
            return jsonify({'success': False, 'error': 'Skill not found'}), 404
        
        employee.set_skills_list(updated_skills)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Skill removed successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error removing skill: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to remove skill'}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(port=5000, debug=True)
