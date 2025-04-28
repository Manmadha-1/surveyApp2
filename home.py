import streamlit as st
st.set_page_config(layout="wide")
import mysql.connector
import json

# Database setup
def setup_database():
    conn = mysql.connector.connect(
        host="surveyapp-db1.ctwkcywuyqju.us-east-1.rds.amazonaws.com",
        user="admin",
        password="TOP2020%"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS surveysDb")
    cursor.execute("USE surveysDb")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question_id INT NOT NULL,
            question_text TEXT,
            response_text TEXT,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    """)
    conn.close()

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="surveyapp-db1.ctwkcywuyqju.us-east-1.rds.amazonaws.com",
        user="admin",
        password="TOP2020%",
        database="surveysDb"
    )

# User Interface
def user_interface():
    # Check if "thank_you" is in session state
    if "thank_you" not in st.session_state:
        st.session_state.thank_you = False

    # If "thank_you" is True, display the Thank You page
    if st.session_state.thank_you:
        st.balloons()
        st.markdown(
            """
            <style>
            .centered {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 80vh;
                text-align: center;
            }
            </style>
            <div class="centered">
                <div>
                    <h1>Thank You!</h1>
                    <p>Your responses have been saved successfully.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Default title
    st.title("Survey Response")
    
    # Step 1: Get survey ID from URL parameters
    query_params = st.query_params
    survey_id = query_params.get("survey_id", [None])[0]  # Get survey_id from URL
    
    if survey_id:
        try:
            survey_id = int(survey_id)  # Ensure survey_id is an integer
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Fetch survey name
            cursor.execute("SELECT name FROM surveys WHERE id = %s", (survey_id,))
            survey = cursor.fetchone()
            
            if survey:
                # Update the title dynamically with the survey name
                st.subheader(f"Survey: :blue[{survey['name']}]")
                
                # Fetch survey questions
                cursor.execute("SELECT * FROM questions WHERE survey_id = %s", (survey_id,))
                questions = cursor.fetchall()
                conn.close()
                
                if questions:
                    responses = {}
                    missing_required = False  # Flag to track missing required responses
                    for question in questions:
                        if question["question_type"] == "picklist":
                            # Render a dropdown for picklist questions
                            options = json.loads(question["picklist_options"]) if question["picklist_options"] else []
                            responses[question["id"]] = st.selectbox(
                                f"{question['question_text']} {' :red[*] (Required)' if question['is_required'] else ''}",
                                options=["-- NONE --"] + options,  # Add an empty option for default
                                key=f"response_{question['id']}",
                            )
                        else:
                            # Render a text input for text questions
                            if question["is_required"]:
                                responses[question["id"]] = st.text_input(f"{question['question_text']} :red[*] (Required)", key=f"response_{question['id']}")
                            else:
                                responses[question["id"]] = st.text_input(f"{question['question_text']}", key=f"response_{question['id']}")
                    
                    # Step 3: Save responses
                    if st.button(":green[Save Responses]"):
                        # Validate required responses
                        for question in questions:
                            if question["is_required"] and not responses[question["id"]].strip():
                                st.warning(f"Please fill in the required question: {question['question_text']}")
                                missing_required = True
                                break
                        
                        if not missing_required:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            for question_id, response in responses.items():
                                # Fetch the question text for the current question ID
                                question_text = next(q["question_text"] for q in questions if q["id"] == question_id)
                                cursor.execute(
                                    "INSERT INTO responses (question_id, question_text, response_text) VALUES (%s, %s, %s)",
                                    (question_id, question_text, response)
                                )
                            conn.commit()
                            conn.close()
                            
                            # Set session state to display Thank You page
                            st.session_state.thank_you = True
                            st.rerun()
                else:
                    st.error("No questions found for this survey.")
            else:
                st.error("Survey not found.")
                conn.close()
        except ValueError:
            st.error("Invalid survey ID.")
    else:
        st.error("No survey ID provided in the URL.")

# Main function
def main():
    setup_database()
    user_interface()

if __name__ == "__main__":
    main()