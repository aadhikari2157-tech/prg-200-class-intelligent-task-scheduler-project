**Intelligent Task Scheduler: A Smart Productivity and Task Management System**

**In step 1 ,**
We set up the project environment. First we created a project folder called task_scheduler using the mkdir command in the terminal. Then we created a virtual environment using python -m venv venv and activated it.
A virtual environment is basically an isolated workspace for our project. It keeps all the libraries we install separate from other Python projects on the computer. This is important for teamwork — everyone on the team works with the same clean setup without libraries from other projects interfering.
we also opened the project in VS Code which is the code editor we used throughout the entire project.

**In step 2 ,**

In Step 2, we installed the project dependencies. These are external libraries developed by other programmers that we used in our project instead of building every feature from scratch.

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






