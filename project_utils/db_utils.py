#This module handles all interactions with the MySQL database
import mysql.connector
from mysql.connector import Error
# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'RITHIkap2006',
    'database': 'aadhaar_verification'
}
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None
    return None
def setup_database():
    conn = None 
    cursor = None 
    try:
        #Connect to MySQL server to create the database if it doesn't exist
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        print(f"Database '{DB_CONFIG['database']}' ensured.")
    except Error as e:
        print(f"Error during database setup: {e}")
        return
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    # Connect to the specific database to create the table
    try:
        conn = get_db_connection()
        if not conn:
            print("Could not connect to the database to set up table. Aborting.")
            return
        cursor = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS verification_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            ai_prediction VARCHAR(50),
            confidence FLOAT,
            ocr_text TEXT,
            final_verdict VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        print("Table 'verification_results' ensured.")
        conn.commit()
    except Error as e:
        print(f"Error creating table: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
def store_verification_result(filename, ai_prediction, confidence, ocr_text, final_verdict):
    """
    Inserts a single verification record into the 'verification_results' table.
    Manages its own database connection to ensure operations are self-contained.
    """
    query = """
    INSERT INTO verification_results (filename, ai_prediction, confidence, ocr_text, final_verdict)
    VALUES (%s, %s, %s, %s, %s)
    """
    args = (filename, ai_prediction, confidence, ocr_text, final_verdict)
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, args)
            conn.commit()
            print(f"Successfully stored result for {filename}")
        except Error as e:
            print(f"Error storing verification result: {e}")
        finally:
            cursor.close()
            conn.close()
def retrieve_all_results():
    query = "SELECT id, filename, ai_prediction, confidence, final_verdict, timestamp FROM verification_results ORDER BY timestamp DESC"
    results_list = []
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            results_list = cursor.fetchall()
        except Error as e:
            print(f"Error retrieving results: {e}")
        finally:
            cursor.close()
            conn.close()
    return results_list