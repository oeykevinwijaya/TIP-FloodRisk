import csv
import os
import mysql.connector
import joblib
import requests
import smtplib
import pandas as pd

from flask import Flask, render_template, jsonify, request
from backend.services.dbconnect import insert_notification_preferences
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Path to the CSV file
data_file_path = os.path.join(os.getcwd(), 'backend/data/userdata.csv')

app = Flask(__name__)
model = joblib.load('backend/models/flood_prediction_model.pkl')
    

@app.route('/predict_flood', methods=['POST'])
def predict_flood_api():
    prediction = predict_flood()
    if prediction is not None:
        return jsonify({'prediction': str(prediction)})
    else:
        return jsonify({'error': 'Failed to make prediction'}), 500

def predict_flood(test_data=None, return_prob=False):
    try:
        if test_data is None:
            # No test data provided, fetch real-time data
            api_url = 'https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en'
            response = requests.get(api_url)
            if response.status_code != 200:
                return None
            real_time_data = response.json()
        else:
            # Use test data provided
            real_time_data = test_data

        feature_vector = extract_feature_vector(real_time_data)
        feature_df = pd.DataFrame([feature_vector], columns=['Rainfall', 'Humidity', 'Year', 'Month', 'Day', 'Temperature'])
        probabilities = model.predict_proba(feature_df)[:, 1]
        prediction = (probabilities > 0.68).astype(int)
        if return_prob:
            return prediction[0], probabilities[0]
        return prediction[0]
    except Exception as e:
        print(str(e))
        return None

# Function to extract feature vector from real-time data
def extract_feature_vector(real_time_data):
    # Extract the temperature, humidity, and rainfall
    temperature = real_time_data['temperature']['data'][0]['value']
    humidity = real_time_data['humidity']['data'][0]['value']
    rainfall = max(item['max'] for item in real_time_data['rainfall']['data'])

   # Safely extract recordTime or use a default
    record_time = real_time_data['temperature'].get('recordTime', "2024-05-08T14:00:00+08:00")
    parsed_date = datetime.strptime(record_time, "%Y-%m-%dT%H:%M:%S+08:00")

    year = parsed_date.year
    month = parsed_date.month
    day = parsed_date.day

    feature_vector = {
        'Rainfall': rainfall,
        'Humidity': humidity,
        'Year': year,
        'Month': month,
        'Day': day,
        'Temperature': temperature
    }
    return feature_vector


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
    # Extract query parameters
    selected_location = request.args.get('location', 'cheung_chau')  # Default to 'cheung_chau' if not provided
    selected_year = request.args.get('year', '2022')  # Set initial value for year
    selected_month = request.args.get('month', '1')  # Set initial value for month

    # Construct CSV file path based on selected location
    csv_file_path = os.path.join(os.getcwd(), f"backend/data/Daily Rainfall/{selected_location}.csv")

    # Check if the file exists
    if not os.path.exists(csv_file_path):
        return f"CSV file not found: {csv_file_path}"

    # List to hold rows of data
    forecasts = []

    # Read CSV data
    try:
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Remove BOM from keys
                row = {key.strip('\ufeff'): value for key, value in row.items()}
                forecasts.append(row)
    except Exception as e:
        return f"Error reading CSV file: {str(e)}"

    # Filter data based on query parameters
    filtered_forecasts = [forecast for forecast in forecasts if forecast['Month'] == selected_month and forecast['Year'] == selected_year]

    # Pass data to the template
    return render_template('history.html', forecasts=filtered_forecasts, selected_year=selected_year, selected_month=selected_month)

@app.route('/history.html')
def historyh():
    # Extract query parameters
    selected_location = request.args.get('location', 'cheung_chau')  # Default to 'cheung_chau' if not provided
    selected_year = request.args.get('year', '2022')  # Set initial value for year
    selected_month = request.args.get('month', '1')  # Set initial value for month

    # Construct CSV file path based on selected location
    csv_file_path = os.path.join(os.getcwd(), f"backend/data/Daily Rainfall/{selected_location}.csv")

    # Check if the file exists
    if not os.path.exists(csv_file_path):
        return f"CSV file not found: {csv_file_path}"

    # List to hold rows of data
    forecasts = []

    # Read CSV data
    try:
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Remove BOM from keys
                row = {key.strip('\ufeff'): value for key, value in row.items()}
                forecasts.append(row)
    except Exception as e:
        return f"Error reading CSV file: {str(e)}"

    # Filter data based on query parameters
    filtered_forecasts = [forecast for forecast in forecasts if forecast['Month'] == selected_month and forecast['Year'] == selected_year]

    # Pass data to the template
    return render_template('history.html', forecasts=filtered_forecasts, selected_year=selected_year, selected_month=selected_month)

@app.route('/get_rainfall_data')
def get_rainfall_data():
    selected_location = request.args.get('location', 'cheung_chau')
    selected_year = request.args.get('year', '2023')
    selected_month = request.args.get('month', '1')

    # Construct the CSV file path based on the selected location
    csv_file_path = os.path.join(os.getcwd(), f"backend/data/Daily Rainfall/{selected_location}.csv")

    if not os.path.exists(csv_file_path):
        return jsonify({'error': f"CSV file not found: {csv_file_path}"})

    forecasts = []
    try:
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                row = {key.strip('\ufeff'): value for key, value in row.items()}
                forecasts.append(row)
    except Exception as e:
        return jsonify({'error': f"Error reading CSV file: {str(e)}"})

    # Filter data based on query parameters
    filtered_forecasts = [forecast for forecast in forecasts if forecast['Month'] == selected_month and forecast['Year'] == selected_year]

    # Prepare the chart data including Year, Month, Day, and Value
    chart_data = [{'YEAR': row['Year'], 'MONTH': row['Month'], 'DAY': row['Day'], 'VALUE': row['Value']} for row in filtered_forecasts]

    return jsonify(chart_data)

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

    # Create CSV file if it doesn't exist
    if not os.path.exists(data_file_path):
        with open(data_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Location', 'Name', 'Email', 'Rainfall Alert', 'Flood Alert'])

    # Append new preferences to the CSV file
    with open(data_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([location, name, email, rainfall, flood])

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
    # Read data from the CSV file
    data = []
    if os.path.exists(data_file_path):
        with open(data_file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data.append(row)

    return render_template('admin_page_alert.html', data=data)

@app.route('/send_notification', methods=['POST'])
def send_notification():
    # Load the recipient email addresses from the CSV file
    recipients = []
    with open('backend/data/userdata.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            recipients.append(row['Email'])

    # Load email subject and body from the CSV file
    with open('backend/data/notification/emaildata.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            subject = row['subject']
            body = row['body']

    # Append the forecast table to the email body
    with open('backend/data/9dforecast.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        table = '<br><br><table border="1">'
        table += '<tr>' + ''.join(f'<th>{key}</th>' for key in csv_reader.fieldnames) + '</tr>'
        for row in csv_reader:
            table += '<tr>' + ''.join(f'<td>{value}</td>' for value in row.values()) + '</tr>'
        table += '</table>'
        body += table

    # Email sender details


    # Send email to each recipient
    for recipient in recipients:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, 'html'))
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, recipient, msg.as_string())
            print(f"Message sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {str(e)}")

    return "Emails sent successfully!"

# Route for send_alert
@app.route('/send_alert', methods=['POST'])
def send_alert():
    # Load the recipient email addresses from the CSV file
    recipients = []
    with open('backend/data/userdata.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            recipients.append(row['Email'])

    # Load email subject and body from the CSV file
    with open('backend/data/notification/rainfallwarning.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            subject = row['subject']
            body = row['body']

    # Email sender details


    # Send email to each recipient
    for recipient in recipients:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, 'html'))
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, recipient, msg.as_string())
            print(f"Message sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {str(e)}")

    return "Emails sent successfully!"


# Route for admin_access.html
@app.route('/admin_access.html', methods=['GET', 'POST'])
def admin_access():
    if request.method == 'POST':
        # Extract username and password from form
        username = request.form.get('username')
        password = request.form.get('password')

        # Simple validation for demonstration purposes
        if username == 'admin' and password == 'password':
            return render_template('admin_access.html')
        else:
            return render_template('loginadmin.html', error='Invalid username or password')

    return render_template('admin_access.html')

@app.route('/loginadmin.html')
def admin_login():
    return render_template('loginadmin.html')

if __name__ == '__main__':
    app.run(debug=True)