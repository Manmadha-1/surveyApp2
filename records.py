import streamlit as st
st.set_page_config(layout="wide")
import mysql.connector
import pandas as pd  # Import pandas for DataFrame manipulation

# Function to establish a connection to the MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host="surveyapp-db1.ctwkcywuyqju.us-east-1.rds.amazonaws.com",       # Replace with your MySQL host
        user="admin",       # Replace with your MySQL username
        password="TOP2020%",  # Replace with your MySQL password
        database="surveysDb"   # Replace with your MySQL database name
    )

# Function to fetch all records from the 'responses' table
def fetch_all_records():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM  responses")  # Replace 'responses' with your table name
        records = cursor.fetchall()
        return records
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Streamlit app
st.title("Show Records from Responses")

# Button to fetch and display records
if st.button("Show Records"):
    records = fetch_all_records()
    if records:
        st.success("Records fetched successfully!")
        # Convert records to a DataFrame and display without index
        df = pd.DataFrame(records)
        df_with_index = df.set_index("id")
        st.write(df_with_index)
    else:
        st.warning("No records found or an error occurred.")