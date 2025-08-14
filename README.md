# Task Manager App

A comprehensive task management system built with Flask featuring role-based dashboards for developers, project managers, and administrators.

## Features

- **Multi-Role Dashboard System**: Separate interfaces for developers, project managers, and admins
- **Task Management**: Create, assign, track, and approve tasks
- **User Authentication**: Secure login system with role-based access
- **FAQ Section**: Built-in help system on all dashboards
- **Dark Theme**: Modern, responsive UI design
- **Employee Management**: Admin tools for managing team members

## Prerequisites

Before running this application, make sure you have:

- **Python 3.8 or higher** installed on your system
- **pip** (Python package installer)
- **Git** (optional, for cloning the repository)

## Installation & Setup

### Step 1: Clone or Download the Project

If using Git:
```bash
git clone <repository-url>
cd Task_Manager_App-1
```

Or download and extract the ZIP file to your desired location.

### Step 2: Create a Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables (Optional)

You can create a `.env` file in the project root directory if you need custom configuration:

```env
SECRET_KEY=your-secret-key-here
EMPLOYEE_SERVICE_URL=http://localhost:5001/api
TASK_SERVICE_URL=http://localhost:5002/api
API_KEY=dev_api_key
```

**Note**: The app will work with default settings if you skip this step.

### Step 5: Initialize the Database

Run the database setup script:

```bash
python setup_db.py
```

### Step 6: Run the Application

Start the Flask development server:

```bash
python main.py
```

The application will be available at: **http://localhost:5000**

## Usage

### Default Login Credentials

After running `setup_db.py`, you can use these default accounts:

- **Admin**: 
  - Email: `admin@example.com`
  - Password: `admin123`

- **Project Manager**: 
  - Email: `manager@example.com` 
  - Password: `manager123`

- **Developer**: 
  - Email: `developer@example.com`
  - Password: `dev123`

### Dashboard Features

#### Developer Dashboard
- View assigned, in-progress, and pending approval tasks
- Submit tasks for review
- Track performance metrics
- Access FAQ section

#### Project Manager Dashboard  
- Create and assign new tasks
- Review and approve submitted tasks
- View team performance analytics
- Manage project types and skills
- Access FAQ section

#### Admin Dashboard
- Manage all employees
- View system-wide statistics
- Update employee metrics
- Filter and search employees
- Access FAQ section

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```
   Error: Address already in use
   ```
   **Solution**: Change the port in `main.py` or kill the process using port 5000:
   ```bash
   # Windows
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   
   # macOS/Linux  
   lsof -ti:5000 | xargs kill -9
   ```

2. **Module Not Found Errors**
   ```
   ModuleNotFoundError: No module named '...'
   ```
   **Solution**: Ensure your virtual environment is activated and dependencies are installed:
   ```bash
   # Activate virtual environment first
   pip install -r requirements.txt
   ```

3. **Database Errors**
   ```
   sqlite3.OperationalError: no such table
   ```
   **Solution**: Run the database setup script:
   ```bash
   python setup_db.py
   ```

4. **Permission Errors (Windows)**
   ```
   PermissionError: [WinError 5] Access is denied
   ```
   **Solution**: Run Command Prompt as Administrator or use PowerShell

### Development Mode

To run in debug mode (auto-reload on file changes):

```bash
export FLASK_DEBUG=1  # Linux/macOS
set FLASK_DEBUG=1     # Windows CMD
$env:FLASK_DEBUG=1    # Windows PowerShell

python main.py
```

## File Structure

```
Task_Manager_App-1/
├── main.py                 # Main Flask application
├── setup_db.py            # Database initialization
├── requirements.txt        # Python dependencies
├── employee_service.py     # Employee management logic
├── email_services.py       # Email functionality
├── task_assignment_service.py  # Task assignment logic
├── templates/              # HTML templates
│   ├── developer_dashboard.html
│   ├── project_manager_dashboard.html
│   ├── admin_dashboard.html
│   └── ...
├── static/                 # Static files (CSS, JS, images)
├── venv/                   # Virtual environment (created after setup)
└── README.md              # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Commit your changes: `git commit -am 'Add some feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

If you encounter any issues or have questions, please create an issue in the repository or contact the development team.