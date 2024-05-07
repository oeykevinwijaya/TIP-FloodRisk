from flask import Flask, render_template, jsonify, request
from backend.services.dbconnect import insert_notification_preferences

import csv
import os
import mysql.connector

app = Flask(__name__)

# Route for landing page
@app.route('/')
def index():
    # Path to CSV file
    csv_file_path = os.path.join(os.getcwd(), 'backend/data/9dforecast.csv')
    
    # List to hold rows of data
    forecasts = []
    
    # Read CSV data
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            forecasts.append(row)
    
    # Pass data to the template
    return render_template('weather_forecast.html', forecasts=forecasts)

# Route for weather forecast page
@app.route('/weather_forecast.html')
def weatherforecast():
    # Path to CSV file
    csv_file_path = os.path.join(os.getcwd(), 'backend/data/9dforecast.csv')
    
    # List to hold rows of data
    forecasts = []
    
    # Read CSV data
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            forecasts.append(row)
    
    # Pass data to the template
    return render_template('weather_forecast.html', forecasts=forecasts)

# Route for history.html
@app.route('/history.html')
def history():
    # Path to CSV file
    # csv_file_path = os.path.join(os.getcwd(), 'backend/data/9dforecast.csv')
    
    # List to hold rows of data
    forecasts = []
    
    # Read CSV data
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            forecasts.append(row)
    
    # Pass data to the template
    return render_template('history.html', forecasts=forecasts)

# Route for warning.html
@app.route ('/warning.html')
def warning():
    return render_template('warning.html')

# Route for faq.html
@app.route ('/faq.html')
def faq():
    return render_template('faq.html')

# Route for noti.html
@app.route ('/noti.html')
def noti():
    return render_template('noti.html')

# Route to handle form submission
@app.route('/submit_preferences', methods=['POST'])
def submit_preferences():
    location = request.form['location']
    name = request.form['name']
    email = request.form['email']
    rainfall = 'rainfall' in request.form
    flood = 'flood' in request.form

    # Insert notification preferences into the database
    insert_notification_preferences(location, name, email, rainfall, flood)

    return render_template('noti.html', success=True)


# Route for contact.html
@app.route ('/contact.html')
def contact():
    return render_template('contact.html')

# Route for email.html
@app.route ('/email.html')
def email():
    return render_template('email.html')

# Route for data_management.html
@app.route ('/data_management.html')
def data_management():
    return render_template('data_management.html')


# Route for admin_page_alert.html
@app.route('/admin_page_alert.html')
def admin_page_alert():
    db_connection = mysql.connector.connect(
        host="feenix-mariadb.swin.edu.au",
        user="s104341635",
        password="swinburne",
        database="s104341635_db"
    )
    cursor = db_connection.cursor()

    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()

    return render_template('admin_page_alert.html', data=data)


# Route for admin_access.html
@app.route ('/admin_access.html')
def admin_access():
    return render_template('admin_access.html')

if __name__ == '__main__':
    app.run(debug=True)
