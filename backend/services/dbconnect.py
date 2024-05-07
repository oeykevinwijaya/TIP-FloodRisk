# sample code to insert data into a MariaDB database table

import mysql.connector

def insert_notification_preferences(location, name, email, rainfall, flood):
    db_connection = mysql.connector.connect(
        host="feenix-mariadb.swin.edu.au",
        user="s104341635",
        password="swinburne",
        database="s104341635_db"
    )

    cursor = db_connection.cursor()

    try:
        sql = "INSERT INTO users (location, name, email, rainfall, flood) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (location, name, email, rainfall, flood))
        db_connection.commit()
        print("Notification preferences inserted successfully!")

    except mysql.connector.Error as error:
        print(f"Error inserting data into MySQL: {error}")
        db_connection.rollback()

    finally:
        if db_connection.is_connected():
            cursor.close()
            db_connection.close()
            print("MySQL connection closed")
