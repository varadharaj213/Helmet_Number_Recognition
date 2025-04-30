from flask import Flask, render_template, request, redirect, url_for, send_file
import mysql.connector
import pandas as pd
import os
import csv
from langchain_community.agent_toolkits import GmailToolkit
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_community.tools.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)

app = Flask(__name__)

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "student"
}

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'  # Change this for security

# File Paths
STUDENT_CSV_PATH = "students.csv"
DEFAULTERS_CSV_PATH = "D:\Helmet_Number_Recognition\matched_students.csv"

# Connect to MySQL Database
def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None

@app.route('/')
def home():
    return redirect(url_for('student_registration'))

@app.route('/register', methods=['GET', 'POST'])
def student_registration():
    if request.method == 'POST':
        connection = connect_db()
        if not connection:
            return "Database connection failed", 500
        
        cursor = connection.cursor()
        data = (
            request.form['name'],
            request.form['register_number'],
            request.form['department'],
            request.form['vehicle_number'],
            request.form['mobile_number'],
            request.form['email']
        )
        
        query = """
        INSERT INTO student_info (Name, RegisterNum, Department, Bikeno, MobileNum, Email)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, data)
        connection.commit()
        connection.close()
        return redirect(url_for('student_registration'))

    return render_template('student_registration.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/download_students')
def download_students():
    connection = connect_db()
    if not connection:
        return "Database connection failed", 500
    
    query = "SELECT Name, RegisterNum as 'Register Number', Department, Bikeno,Email, MobileNum FROM student_info"
    df = pd.read_sql(query, connection)
    df.to_csv(STUDENT_CSV_PATH, index=False)
    connection.close()
    
    return send_file(STUDENT_CSV_PATH, as_attachment=True)

@app.route('/defaulters')
def defaulters():
    defaulters_list = []
    if os.path.exists(DEFAULTERS_CSV_PATH):
        with open(DEFAULTERS_CSV_PATH, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                defaulters_list.append(row)
    
    return render_template('defaulters.html', defaulters=defaulters_list)

# ----------------- EMAIL SENDING FUNCTION -----------------

# Get Gmail credentials
credentials = get_gmail_credentials(
    token_file="token.json",
    scopes=["https://mail.google.com/"],
    client_secrets_file="cred.json",
)

# Build API resource
api_resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=api_resource)
tools = toolkit.get_tools()

# Initialize LLM
llm = ChatGroq(
    model="gemma2-9b-it",
    api_key="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"  # Replace with a valid API key
)

def send_violation_mails(defaulters_filename='D:\Helmet_Number_Recognition\matched_students.csv'):
    agent_executor = create_react_agent(llm, tools)

    with open(defaulters_filename, mode='r') as file:
        reader = csv.reader(file)
        header = next(reader)
        
        # Extract column indices
        name_index = header.index("Name")
        reg_no_index = header.index("Register Number")
        vehicle_no_index = header.index("Vehicle Number")
        dept_index = header.index("Department")
        email_index = header.index("Email")
        datetime_index = header.index("Date/Time")
        
        for row in reader:
            name = row[name_index]
            reg_no = row[reg_no_index]
            vehicle_no = row[vehicle_no_index]
            department = row[dept_index]
            email_id = row[email_index]
            datetime = row[datetime_index]
            
            violation_query = f'''
            Send an email to {email_id} informing them about a rule violation.
            Email format:
            - Subject: Helmet Rule Violation Notice
            - Greeting: Dear {name},
            - Content: Inform them that they have been found violating the helmet rule on {datetime}.
            - Details: Include their Register Number ({reg_no}), Department ({department}), and Vehicle Number ({vehicle_no}).
            - Warning: Emphasize the importance of following safety rules and mention potential consequences for repeat offenses.
            - Closing: Sign off with a polite message from the concerned authority.
            Directly send it, don't ask for a review.
            '''
            
            events = agent_executor.stream(
                {"messages": [("user", violation_query)]},
                stream_mode="values",
            )
            
            for event in events:
                print(event["messages"][-1])

    print("Violation emails have been sent.")

@app.route('/send_violation_emails', methods=['POST'])
def send_violation_emails():
    try:
        send_violation_mails()  # Call the function to send emails
        return redirect(url_for('defaulters'))  # Redirect back after sending emails
    except Exception as e:
        return f"Error sending emails: {str(e)}", 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
