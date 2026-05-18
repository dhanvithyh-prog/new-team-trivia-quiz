import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="SCT and RIA team Trivia", layout="centered")

# Securely grab database credentials from Streamlit Secrets
UPSTASH_URL = st.secrets["UPSTASH_URL"]
UPSTASH_TOKEN = st.secrets["UPSTASH_TOKEN"]
HEADERS = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

quiz_data = {
    "Q1: What year was Motorola Solutions founded?": [["1960", "1928", "1935", "1915"], "1928"],
    
}

questions_list = list(quiz_data.keys())

# --- SESSION STATE INITIALIZATION ---
if 'player_name' not in st.session_state:
    st.session_state.player_name = ""
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'answered_current' not in st.session_state:
    st.session_state.answered_current = False

# Custom CSS for UI animations and styling
st.markdown("""
    <style>
    @keyframes pulse {
        0% { transform: scale(1); text-shadow: 0 0 10px #FFD700; }
        50% { transform: scale(1.05); text-shadow: 0 0 20px #FFD700, 0 0 30px #FF8C00; }
        100% { transform: scale(1); text-shadow: 0 0 10px #FFD700; }
    }
    .champion-text {
        animation: pulse 2s infinite;
        color: #FFD700;
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏆 SCT and RIA team Trivia")

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
    st.progress((st.session_state.current_q_index) / len(questions_list))
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
        else:
            st.error(f"❌ Incorrect. The correct answer was **{correct_answer}**.")
            
        if st.button("Next Question ➡️", type="primary"):
            st.session_state.current_q_index += 1
            st.session_state.answered_current = False
            st.rerun()

# --- SCREEN 3: END GAME / LEADERBOARD ---
else:
    st.success("🎉 You have completed the trivia!")
    st.divider()
    st.header("👑 Global Leaderboard")
    
    with st.spinner("Fetching live scores..."):
        try:
            response = requests.get(f"{UPSTASH_URL}/lrange/trivia_answers/0/-1", headers=HEADERS)
            if response.status_code == 200:
                raw_data = response.json().get("result", [])
                
                if raw_data:
                    parsed_data = [json.loads(item) for item in raw_data]
                    df = pd.DataFrame(parsed_data)
                    
                    # Calculate Leaderboard
                    leaderboard = df.groupby("Who")["Points"].sum().sort_values(ascending=False).reset_index()
                    
                    # 1. Create Serial Numbers / Ranks (1, 2, 3...)
                    leaderboard.index = leaderboard.index + 1
                    leaderboard.reset_index(inplace=True)
                    leaderboard.rename(columns={'index': 'Rank'}, inplace=True)
                    
                    # 2. Add Medals for Top 3
                    def get_medal(rank):
                        if rank == 1: return "🥇 1"
                        elif rank == 2: return "🥈 2"
                        elif rank == 3: return "🥉 3"
                        else: return str(rank)
                        
                    leaderboard['Rank'] = leaderboard['Rank'].apply(get_medal)
                    leaderboard['Points'] = leaderboard['Points'].astype(int)
                    
                    # Announce Champion with CSS Animation
                    if not leaderboard.empty:
                        winner = leaderboard.iloc[0]['Who']
                        score = leaderboard.iloc[0]['Points']
                        st.markdown(f"<div class='champion-text'>🏆 {winner} Wins ({score} pts)! 🏆</div>", unsafe_allow_html=True)
                    
                    # 3. Display beautiful dataframe without the default Pandas index
                    st.dataframe(
                        leaderboard, 
                        hide_index=True, 
                        use_container_width=True,
                        column_config={
                            "Rank": st.column_config.TextColumn("Rank", width="small"),
                            "Who": st.column_config.TextColumn("Player Name", width="large"),
                            "Points": st.column_config.NumberColumn("Total Score", format="%d", width="medium")
                        }
                    )
                    
                else:
                    st.info("No scores found yet! Waiting for players to finish...")
            else:
                st.error("Failed to fetch the leaderboard.")
        except Exception as e:
            st.error(f"Couldn't load the leaderboard. Check your connection. {e}")
            
    st.divider()
    if st.button("🔄 Refresh Leaderboard"):
        st.rerun()
        
    if st.button("Play Again (Restart)"):
        st.session_state.clear()
        st.rerun()
