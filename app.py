import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Motorola Team Trivia", layout="wide")

# Connect to your Google Apps Script Web App
WEB_APP_URL = "https://script.google.com/a/macros/motorolasolutions.com/s/AKfycbw7SzMsNPz2bhH72fVkcUKnJdGm7ONTcm5hSuw9OB1iZT_x9dMigM9FbqcrAMJfMDUWjA/exec"

# 1. Setup Questions + The Correct Answer
quiz_data = {
    "Q1: What year was Motorola Solutions founded?": [["1960", "1928", "1935", "1915"], "1928"],
    "Q2: In the 1990s, Motorola introduced a communication device that became a massive pop culture phenomenon, eventually controlling 80% of the global market for this technology. What was it?": [["The Pager", "The Walkman", "The CB Radio", "The Fax Machine"], "The Pager"],
    "Q3: Motorola Solutions’ products have a legacy of operating in extreme conditions. In fact, our equipment transmitted famous audio from where?": [["The bottom of the Mariana Trench", "Mount Everest's summit", "The Moon (Neil Armstrong's first words)","The Titanic wreckage"], "The Moon (Neil Armstrong's first words)"],
    "Q4: In 2011, the original Motorola Inc. split into two completely separate companies. We are Motorola Solutions. What was the other one called?": [["Motorola Communications", "Motorola Mobility", "Motorola Consumer", "Motorola Devices"], "Motorola Mobility"],
    "Q5: We sell the HALO Smart Sensor for schools and hospitals. What makes it so unique compared to our other Avigilon security cameras?": [["It floats using magnets", "It has absolutely no video or lenses", "It only shoots in black and white", "It is disguised as a smoke detector"], "It has absolutely no video or lenses"],
    "Q6: What is the name of MSI's custom-built, mission-critical AI engine used to help first responders and generate incident narratives?": [["Skynet", "ChatGPT", "Moto-Bot", "Assist "], "Assist "],
    "Q7: Where is Motorola Solutions' global headquarters located?": [["Schaumburg", "Chicago", "Austin", "San Jose"], "Chicago"],
    "Q8: During World War II, Motorola produced the SCR-300, which became a legendary and vital piece of communication equipment. What was it?": [["A portable radar system", "An early code-breaking machine", "The first portable, FM, backpack two-way radio", "A sonar device for submarines"], "The first portable, FM, backpack two-way radio"],
    "Q9: What was price of first Motorola public stock sold in 1943?": [["5", "8.5", "10", "6.5"], "8.5"],
    "Q10: What is the official internal nickname for the iconic Motorola 'M' logo?": [["The Twin Peaks", "The Arch", "The Batwing", "The Sonic Wave"], "The Batwing"]
}

# Local state to prevent a user from spam-clicking submit on one question
if 'answered_questions' not in st.session_state:
    st.session_state.answered_questions = set()

# 2. Sidebar: Identity & Navigation
st.sidebar.title("👤 Player Info")
user_name = st.sidebar.text_input("Enter your name:", key="user_name")

st.sidebar.divider()
current_q = st.sidebar.radio("Select Question:", list(quiz_data.keys()))

# 3. Main Quiz Area
st.title("🏆 Motorola Team Trivia")

if not user_name:
    st.warning("Please enter your name in the sidebar to join the game!")
else:
    options, correct_answer = quiz_data[current_q]
    
    # Check if user already answered this in their current session
    question_key = f"{user_name}_{current_q}"
    
    if question_key in st.session_state.answered_questions:
        st.info("You have already answered this question! Head to the next one.")
    else:
        with st.form(key=f"form_{current_q}", clear_on_submit=False):
            st.subheader(current_q)
            choice = st.radio("Your Answer:", options)
            submit = st.form_submit_button("Submit Answer")

        if submit:
            is_correct = (choice == correct_answer)
            
            # Prepare the JSON payload to send to Google Sheets
            payload = {
                "Who": user_name,
                "Question": current_q,
                "Answer": choice,
                "IsCorrect": is_correct,
                "Points": 1 if is_correct else 0
            }
            
            with st.spinner("Saving answer..."):
                try:
                    # POST request to Google Apps Script
                    response = requests.post(WEB_APP_URL, json=payload)
                    
                    if response.status_code == 200:
                        st.session_state.answered_questions.add(question_key)
                        if is_correct:
                            st.success("🎯 Correct!")
                            st.balloons()
                        else:
                            st.error("❌ Not quite!")
                    else:
                        st.error("Database connection failed. Please try again.")
                except Exception as e:
                    st.error(f"Error saving answer: {e}")

# 4. LEADERBOARD (Now fetching globally from Google Sheets)
st.sidebar.divider()
if st.sidebar.button("📊 SHOW LEADERBOARD"):
    st.header("👑 Global Leaderboard")
    
    with st.spinner("Fetching live scores..."):
        try:
            # GET request to pull data from Google Sheets
            response = requests.get(WEB_APP_URL)
            data = response.json()
            
            # data[0] contains the headers, data[1:] contains the rows
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                
                # Ensure Points column is treated as numbers so we can sum it
                df['Points'] = pd.to_numeric(df['Points'])
                
                # Group by Name and sum the points
                leaderboard = df.groupby("Who")["Points"].sum().sort_values(ascending=False).reset_index()
                
                st.table(leaderboard)
                st.bar_chart(leaderboard.set_index("Who"))
                
                if not leaderboard.empty:
                    winner = leaderboard.iloc[0]['Who']
                    st.markdown(f"## 🏆 The Current Leader is **{winner}**! 🏆")
            else:
                st.write("No scores recorded yet! Be the first to answer.")
                
        except Exception as e:
            st.error("Couldn't load the leaderboard. Check your Web App URL permissions.")
