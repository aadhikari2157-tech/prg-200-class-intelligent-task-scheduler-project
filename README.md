**Intelligent Task Scheduler: A Smart Productivity and Task Management System**

**In step 1 ,**

We set up the project environment. First we created a project folder called task_scheduler using the mkdir command in the terminal. Then we created a virtual environment using python -m venv venv and activated it.
A virtual environment is basically an isolated workspace for our project. It keeps all the libraries we install separate from other Python projects on the computer. This is important for teamwork — everyone on the team works with the same clean setup without libraries from other projects interfering.
we also opened the project in VS Code which is the code editor we used throughout the entire project.

**In step 2 ,**

we installed the project dependencies. These are external libraries developed by other programmers that we used in our project instead of building every feature from scratch.

We used the command: **pip install flask flask-sqlalchemy flask-login werkzeug**
pip is Python's package manager, which downloads and installs libraries from online repositories.

We installed four main libraries:

- Flask is the web framework used in our project. It starts the web server, handles requests from the browser, and determines which function should run for a specific URL. Without Flask, handling browser requests would require a large amount of low-level programming.
- Flask-SQLAlchemy is an Object Relational Mapper (ORM). It acts as a bridge between our Python code and the database. Instead of writing raw SQL queries, we can work with Python objects, and Flask-SQLAlchemy automatically translates them into database operations.
- Flask-Login manages user authentication and sessions. It remembers which user is currently logged in and provides features such as @login_required to restrict access to protected pages and current_user to identify the active user.
- Werkzeug provides security utilities that we use for password hashing. Rather than storing passwords in plain text, we convert them into secure hashed values. This helps protect user accounts because even if the database is compromised, the original passwords cannot be easily recovered.

**Finally, we ran**
pip freeze > requirements.txt (This command saves the exact versions of all installed libraries into a requirements.txt file. This is important for team collaboration because any team member can download the project and run)

pip install -r requirements.txt (to install the same versions of all dependencies and ensure that the application runs consistently across different development environments.)

**Step 3 – Create the Data Models (models.py)**
In this step, we defined the database structure of our application by creating the models.py file. This file tells the database what tables to create and what columns each table should have.

**What is a Model?**

A model is a Python class that represents a database table. Each attribute in the class becomes a column in the table. We used Flask-SQLAlchemy to define our models, which automatically translates these Python classes into actual database tables without writing any SQL.

**Models We Created**

We created three models in this file:
1. User
Stores account information for every registered user. Contains the username, email, and hashed password. It also has a relationship to the Task model so that every user is connected to their own tasks.
2. Task
The main model of the application. Stores everything about a task including the title, priority level (High, Medium, Low), current status (Pending, In Progress, Done), due date, start time, end time, creation date, and completion date. Each task is linked to a specific user through a foreign key so users only see their own tasks.
3. Notification
Stores system-generated alerts for each user. When a task becomes overdue or its deadline is approaching, the system automatically creates a notification record in this table. Each notification is linked to both the user and the specific task it refers to, and tracks whether the user has read it or not.

**Why Three Separate Tables?**

Separating data into three tables follows the database normalization principle. Instead of storing everything in one large table, we keep related data together and link tables using foreign keys. This avoids data duplication, makes queries faster, and keeps the database organized.

Key Concepts Used

- db.Column — defines a column with a specific data type and constraints
- db.ForeignKey — creates a link between two tables
- db.relationship — allows accessing related records using Python dot notation (e.g. user.tasks)
- UserMixin — provided by Flask-Login, gives the User model built-in authentication helper methods such as is_authenticated and is_active
- default=datetime.utcnow — automatically records the exact time a record was created without any manual input

**How the Database Gets Created**

The actual database file (tasks.db) is not created in this step. It is created later when app.py runs db.create_all(), which reads these model definitions and automatically generates the corresponding SQLite database tables.

**Step 4 – Create the Scheduling Algorithm (scheduler.py)**

In this step, we created the brain of our application — the scheduler.py file. This file contains all the logic that makes our task scheduler intelligent. It automatically calculates which tasks are most important and tells the user what to focus on first.

**What Does This File Do?**

Instead of showing tasks in the order they were added, this file analyzes every task and assigns it a score. Tasks with higher scores appear at the top. The user never has to manually sort or organize their tasks — the system does it automatically.

**Functions We Created**

**1. calculate_duration_minutes()**

Converts the start time and end time of a task into total minutes. For example a task from 10:00 to 11:30 returns 90 minutes. This value is used by the scoring system to give shorter tasks a slight advantage when scores are tied.

**2. score()**

The most important function in the entire project. It calculates a smart score for every task using five factors:

Priority weight — High priority tasks start with 30 points, Medium with 20, Low with 10
Student weightage — A value from 1 to 10 set manually by the student. Multiplied by 3 so it has real impact. A Kings College student rates how personally important this task is to them — a final exam gets 10, optional reading gets 1
Urgency — Based on exact hours remaining until the deadline. Overdue tasks get 50 points, tasks due within 24 hours get 40 points, tasks due within 48 hours get 30 points, tasks due within a week get 15 points
Duration bonus — Tasks that take 30 minutes or less get 5 bonus points. Tasks between 30 and 60 minutes get 3 bonus points
Age bonus — Every day a task sits unfinished it gains 1 point up to a maximum of 10. This prevents older tasks from being forgotten forever

**3. prioritize_tasks()**

Takes all pending tasks and sorts them using the score function. Uses a five-level system so tasks only collide and use the tiebreaker when their weightage is also equal:

Highest score wins
Higher weightage wins
Earlier deadline wins
Shorter duration wins
Oldest task wins

**4. get_todays_tasks()**

Filters and returns only the tasks that are due today. These are shown separately at the top of the task list on the dashboard.








