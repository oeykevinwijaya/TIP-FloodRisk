from flask import Flask, render_template, jsonify
import csv
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Path to your CSV file
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

@app.route('/history.html')
def history():
    # Path to your CSV file
    csv_file_path = os.path.join(os.getcwd(), 'backend/data/9dforecast.csv')
    
    # List to hold rows of data
    forecasts = []
    
    # Read CSV data
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            forecasts.append(row)
    
    # Pass data to the template
    return render_template('history.html', forecasts=forecasts)

if __name__ == '__main__':
    app.run(debug=True)
