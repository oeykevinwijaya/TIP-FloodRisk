# sample code to insert data into a MariaDB database table

import mysql.connector

# Establish database connection
db_connection = mysql.connector.connect(
    host="feenix-mariadb.swin.edu.au",
    user="s104341635",
    password="swinburne",
    database="s104341635_db"
)

# Create a cursor object
cursor = db_connection.cursor()

try:
    # Create a dummy data list
    dummy_data = [
        ("John Doe", 25, "john@example.com"),
        ("Jane Smith", 30, "jane@example.com"),
        ("Michael Johnson", 40, "michael@example.com")
    ]

    # Insert data into a table
    for data in dummy_data:
        sql = "INSERT INTO users (name, age, email) VALUES (%s, %s, %s)"
        cursor.execute(sql, data)

    # Commit changes
    db_connection.commit()
    print("Dummy data inserted successfully!")

except mysql.connector.Error as error:
    print(f"Error inserting data into MySQL: {error}")
    db_connection.rollback()  # Rollback changes in case of error

finally:
    if db_connection.is_connected():
        cursor.close()
        db_connection.close()
        print("MySQL connection closed")
