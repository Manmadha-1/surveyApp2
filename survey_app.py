import streamlit as st
import mysql.connector
import json  # To store picklist options as JSON in the database

st.set_page_config(layout="wide")

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
        CREATE TABLE IF NOT EXISTS surveys (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            published BOOLEAN DEFAULT FALSE -- Add published column
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            survey_id INT NOT NULL,
            question_text VARCHAR(500) NOT NULL,
            question_type ENUM('text', 'picklist') NOT NULL DEFAULT 'text', -- Add question type
            is_required BOOLEAN NOT NULL,
            picklist_options TEXT, -- Store picklist options as JSON
            UNIQUE (question_text, survey_id), -- Ensure unique questions per survey
            FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE
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

# Admin Management Console
def admin_console():
    st.title("Admin Management Console")
    
    # Step 1: Create a new survey
    survey_name = st.text_input("Enter Survey Name (Required):")
    if st.button("Create Survey"):
        if survey_name:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO surveys (name) VALUES (%s)", (survey_name,))
            conn.commit()
            survey_id = cursor.lastrowid  # Automatically retrieve the new survey ID
            conn.close()
            st.success(f"Survey '{survey_name}' created successfully with ID {survey_id}!")
        else:
            st.error("Survey name cannot be empty.")
    
    # Step 2: Manage questions dynamically
    if survey_name:  # Check if a survey name is provided
        st.subheader("Manage Questions for the Survey")
        
        # Initialize session state for questions
        if "questions" not in st.session_state:
            st.session_state.questions = [{"text": "", "type": "text", "required": False, "options": []} for _ in range(4)]  # Default 4 questions
        
        # Display questions
        for i, question in enumerate(st.session_state.questions):
            col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
            with col1:
                question["text"] = st.text_input(f"Question {i + 1}", value=question["text"], key=f"question_text_{i}")
            with col2:
                question["type"] = st.selectbox(
                    "Type", 
                    ["text", "picklist"], 
                    index=0 if question["type"] == "text" else 1, 
                    key=f"question_type_{i}"
                )
            with col3:
                question["required"] = st.checkbox("Required", value=question["required"], key=f"question_required_{i}")
            with col4:
                if st.button("❌ Remove", key=f"remove_question_{i}"):
                    st.session_state.questions.pop(i)
                    st.rerun()
            
            # If the question type is "picklist", allow the admin to enter options
            if question["type"] == "picklist":
                st.write(f"Picklist Options for Question {i + 1}")
                if "options" not in question or not isinstance(question["options"], list):
                    question["options"] = []
                option_col1, option_col2 = st.columns([4, 2])
                new_option = option_col1.text_input(f":blue[Add Option for Question {i + 1}]", key=f"new_option_{i}")
                if option_col2.button(":green[Add Option]", key=f"add_option_{i}"):
                    if new_option.strip():
                        question["options"].append(new_option.strip())
                        st.rerun()
                # Display existing options
                for j, option in enumerate(question["options"]):
                    opt_col1, opt_col2 = st.columns([2, 2])
                    opt_col1.write(option)
                    if opt_col2.button(":red[Remove]", key=f"remove_option_{i}_{j}"):
                        question["options"].pop(j)
                        st.rerun()
        
        # Add a new question
        if st.button("➕ Add Question"):
            st.session_state.questions.append({"text": "", "type": "text", "required": False, "options": []})
            st.rerun()
        
        # Save questions to the database
        if st.button("Save Questions"):
            valid_questions = [q for q in st.session_state.questions if q["text"].strip()]
            if valid_questions:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Retrieve the survey ID
                cursor.execute("SELECT id FROM surveys WHERE name = %s", (survey_name,))
                survey = cursor.fetchone()
                
                if survey:
                    survey_id = survey[0]
                    for question in valid_questions:
                        cursor.execute(
                            "SELECT id FROM questions WHERE question_text = %s AND survey_id = %s",
                            (question["text"], survey_id)
                        )
                        existing_question = cursor.fetchone()
                        
                        if not existing_question:
                            cursor.execute(
                                "INSERT INTO questions (survey_id, question_text, question_type, is_required, picklist_options) VALUES (%s, %s, %s, %s, %s)",
                                (
                                    survey_id, 
                                    question["text"], 
                                    question["type"], 
                                    question["required"], 
                                    json.dumps(question["options"]) if question["type"] == "picklist" else None
                                )
                            )
                    conn.commit()
                    conn.close()
                    st.success("Questions saved successfully!")
                else:
                    st.error("Failed to retrieve survey ID. Please try again.")
            else:
                st.error("At least one valid question is required.")
        
        # Publish the survey
        if st.button("Publish Survey"):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Retrieve the survey ID
            cursor.execute("SELECT id FROM surveys WHERE name = %s", (survey_name,))
            survey = cursor.fetchone()
            
            if survey:
                survey_id = survey[0]
                
                # Check if the survey has at least one question
                cursor.execute("SELECT COUNT(*) FROM questions WHERE survey_id = %s", (survey_id,))
                question_count = cursor.fetchone()[0]
                
                if question_count > 0:
                    cursor.execute("UPDATE surveys SET published = TRUE WHERE id = %s", (survey_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Survey '{survey_name}' has been published!")
                    
                else:
                    conn.close()
                    st.error("At least one question is required to publish the survey.")
            else:
                st.error("Failed to retrieve survey ID. Please try again.")

# Main function
def main():
    setup_database()
    admin_console()
    

if __name__ == "__main__":
    main()