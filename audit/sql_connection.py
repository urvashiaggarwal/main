import mysql.connector
from mysql.connector import Error

def create_mysql_connection():
    print("Attempting to connect to MySQL...")

    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',  
            database='audit',
            connection_timeout=5,  
            use_pure=True
        )

        print("Connection object created.")
        connection.ping(reconnect=True, attempts=3, delay=2)
        print("Ping to server successful.")

        if connection.is_connected():
            print("Successfully connected to MySQL!")
            cursor = connection.cursor()
            cursor.execute("SELECT NOW();")
            result = cursor.fetchone()
            print("Server time:", result)
            cursor.close()
            return connection
        else:
            print("Connection not established.")
            return None

    except Error as e:
        print("Error while connecting:", e)
        return None

def insert(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users;")
    rows = cursor.fetchall()
    print(" Users table:", rows)


if __name__ == "__main__":
    connection = create_mysql_connection()
    if connection is not None and connection.is_connected():
        insert(connection)
        connection.close()
        print(" Connection closed.")
