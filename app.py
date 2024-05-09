from flask import Flask, render_template, jsonify, request
from backend.services.dbconnect import insert_notification_preferences
from datetime import datetime
import pandas as pd

import csv
import os
import mysql.connector
import joblib
import requests

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
    
    # Call the prediction function and store the result
    prediction_result = predict_flood()  # Ensure this function returns just the prediction or adjust as needed
    
    # Pass data to the template, including the prediction result
    return render_template('weather_forecast.html', forecasts=forecasts, prediction=prediction_result)


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



@app.route('/get_rainfall_data')
def get_rainfall_data():
    # Extract query parameters
    selected_location = request.args.get('location', 'cheung_chau')
    selected_year = request.args.get('year', '2023')  # Default to '2023' if not provided
    selected_month = request.args.get('month', '1')  # Default to '1' if not provided

    # Construct CSV file path based on selected location
    csv_file_path = os.path.join(os.getcwd(), f"backend/data/Daily Rainfall/{selected_location}.csv")

    # Check if the file exists
    if not os.path.exists(csv_file_path):
        return jsonify({'error': f"CSV file not found: {csv_file_path}"})

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
        return jsonify({'error': f"Error reading CSV file: {str(e)}"})

    # Filter data based on query parameters
    filtered_forecasts = [forecast for forecast in forecasts if forecast['Month'] == selected_month and forecast['Year'] == selected_year]

    # Process the data to match the format expected by Chart.js
    chart_data = [{'MONTH': row['Month'], 'VALUE': row['Value']} for row in filtered_forecasts]

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


# Route for admin_access.html
@app.route ('/admin_access.html')
def admin_access():
    return render_template('admin_access.html')

if __name__ == '__main__':
    app.run(debug=True)
