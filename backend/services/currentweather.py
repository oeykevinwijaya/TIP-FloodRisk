import requests
import json
import csv
from datetime import datetime
import pandas as pd

# Fetch JSON data from the API
url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en"
response = requests.get(url)
data = response.json()

# Extract rainfall data
rainfall_data = data["rainfall"]["data"]

# Extract temperature data
temperature_data = data["temperature"]["data"]

# Define CSV file paths
rainfall_csv_file = "backend/data/currentrain.csv"
temperature_csv_file = "backend/data/currenttemp.csv"
rainplace_csv_file = "backend/data/rainplace.csv"

# Function to format date
def format_date(date_str):
    # Convert date string to datetime object
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    # Format the date as "day month year" (e.g., "30 April 2024")
    formatted_date = date_obj.strftime("%d %B %Y")
    return formatted_date

# Write rainfall data to CSV
with open(rainfall_csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Place", "Rainfall (mm)", "Main"])
    for entry in rainfall_data:
        place = entry["place"]
        rainfall = entry["max"]
        main = entry["main"]
        writer.writerow([place, rainfall, main])

# Write temperature data to CSV
with open(temperature_csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Place", "Temperature (°C)"])
    for entry in temperature_data:
        place = entry["place"]
        temperature = entry["value"]
        writer.writerow([place, temperature])

print("Rainfall data saved successfully at:", rainfall_csv_file)
print("Temperature data saved successfully at:", temperature_csv_file)

# Read data from currentrain.csv and hkdistrict.csv
currentrain_df = pd.read_csv(rainfall_csv_file)
hkdistrict_df = pd.read_csv("backend/data/hkdistrict.csv")

# Merge data on the 'Place' column
merged_df = pd.merge(hkdistrict_df, currentrain_df, on='Place', how='left')

# Output merged data to rainplace.csv
merged_df.to_csv(rainplace_csv_file, index=False)

print("Merged data saved successfully at:", rainplace_csv_file)
