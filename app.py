import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="Motorola Team Trivia", layout="centered")

# Securely grab database credentials from Streamlit Secrets
UPSTASH_URL = st.secrets["UPSTASH_URL"]
UPSTASH_TOKEN = st.secrets["UPSTASH_TOKEN"]
HEADERS = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

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

questions_list = list(quiz_data.keys())

# --- SESSION STATE INITIALIZATION ---
if 'player_name' not in st.session_state:
    st.session_state.player_name = ""
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'answered_current' not in st.session_state:
    st.session_state.answered_current = False

st.title("🏆 Motorola Team Trivia")

# --- SCREEN 1: LOGIN ---
if not st.session_state.player_name:
    st.write("Welcome to the challenge! Enter your name to begin.")
    name_input = st.text_input("Your Name:")
    if st.button("Start Game"):
        if name_input.strip() != "":
            st.session_state.player_name = name_input.strip()
            st.rerun()
        else:
            st.warning("Please enter a valid name!")

# --- SCREEN 2: ACTIVE QUIZ ---
elif st.session_state.current_q_index < len(questions_list):
    current_q = questions_list[st.session_state.current_q_index]
    options, correct_answer = quiz_data[current_q]
    
    st.write(f"👤 Playing as: **{st.session_state.player_name}** | Question {st.session_state.current_q_index + 1} of {len(questions_list)}")
    st.divider()

    if not st.session_state.answered_current:
        with st.form(key=f"form_{current_q}"):
            st.subheader(current_q)
            choice = st.radio("Select your answer:", options, index=None)
            submit = st.form_submit_button("Lock it in!")

        if submit:
            if choice is None:
                st.warning("Please select an answer before submitting!")
            else:
                is_correct = (choice == correct_answer)
                payload = {
                    "Who": st.session_state.player_name,
                    "Question": current_q,
                    "Answer": choice,
                    "Points": 1 if is_correct else 0
                }
                
                with st.spinner("Recording answer..."):
                    try:
                        # Push the answer to our Upstash Redis list
                        response = requests.post(
                            f"{UPSTASH_URL}/lpush/trivia_answers", 
                            headers=HEADERS, 
                            data=json.dumps(payload)
                        )
                        if response.status_code == 200:
                            st.session_state.answered_current = True
                            st.session_state.last_was_correct = is_correct
                            st.rerun()
                        else:
                            st.error("Failed to connect to the database. Try again.")
                    except Exception as e:
                        st.error(f"Error saving answer: {e}")
                        
    else:
        st.subheader(current_q)
        if st.session_state.last_was_correct:
            st.success(f"🎯 Correct! The answer was **{correct_answer}**.")
            if st.session_state.current_q_index == 0: 
                st.balloons() 
        else:
            st.error(f"❌ Incorrect. The correct answer was **{correct_answer}**.")
            
        if st.button("Next Question ➡️", type="primary"):
            st.session_state.current_q_index += 1
            st.session_state.answered_current = False
            st.rerun()

# --- SCREEN 3: END GAME / LEADERBOARD ---
else:
    st.success("🎉 You have completed the trivia!")
    st.balloons()
    st.divider()
    st.header("👑 Global Leaderboard")
    
    with st.spinner("Fetching live scores..."):
        try:
            # Get all answers from the Redis list
            response = requests.get(f"{UPSTASH_URL}/lrange/trivia_answers/0/-1", headers=HEADERS)
            if response.status_code == 200:
                raw_data = response.json().get("result", [])
                
                if raw_data:
                    # Convert list of JSON strings back into Python dictionaries
                    parsed_data = [json.loads(item) for item in raw_data]
                    df = pd.DataFrame(parsed_data)
                    
                    # Group by Who and sum the points
                    leaderboard = df.groupby("Who")["Points"].sum().sort_values(ascending=False).reset_index()
                    
                    st.table(leaderboard.style.format({"Points": "{:.0f}"}))
                    
                    if not leaderboard.empty:
                        winner = leaderboard.iloc[0]['Who']
                        st.markdown(f"### 🏆 The Current Champion is **{winner}**! 🏆")
                else:
                    st.write("No scores found yet!")
            else:
                st.error("Failed to fetch the leaderboard.")
        except Exception as e:
            st.error(f"Couldn't load the leaderboard. Check your connection. {e}")
            
    if st.button("Play Again (Restart)"):
        st.session_state.clear()
        st.rerun()
