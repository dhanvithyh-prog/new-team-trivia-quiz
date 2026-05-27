import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="SCT and RIA Teams Trivia", layout="centered")

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
TOTAL_Q = len(questions_list)

# --- SESSION STATE INITIALIZATION ---
if 'player_name' not in st.session_state:
    st.session_state.player_name = ""
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'answered_current' not in st.session_state:
    st.session_state.answered_current = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Custom CSS
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

# --- SCREEN 2: PRESENTER DASHBOARD (SECRET BACKDOOR) ---
elif st.session_state.is_admin:
    st.title("🎛️ Presenter Dashboard")
    st.info("You are in Admin Mode. Your team cannot see this screen.")
    
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        st.markdown("### 📊 Live Event Status")
    with col_btn2:
        if st.button("🔄 Refresh Live Data", type="primary", use_container_width=True):
            st.rerun()
        
    st.divider()
    
    with st.spinner("Fetching live server data..."):
        try:
            response = requests.get(f"{UPSTASH_URL}/lrange/trivia_answers/0/-1", headers=HEADERS)
            if response.status_code == 200:
                raw_data = response.json().get("result", [])
                
                if raw_data:
                    parsed_data = [json.loads(item) for item in raw_data]
                    df = pd.DataFrame(parsed_data)
                    
                    # Group by player to get their current score and questions answered
                    admin_board = df.groupby("Who").agg(
                        Points=('Points', 'sum'),
                        Questions_Answered=('Question', 'count')
                    ).reset_index()
                    
                    admin_board = admin_board.sort_values(by="Points", ascending=False)
                    
                    # Top-level metrics
                    total_players = len(admin_board)
                    finished_players = len(admin_board[admin_board['Questions_Answered'] == TOTAL_Q])
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("👥 Active Players", total_players)
                    col2.metric("✅ Completed Quiz", f"{finished_players} / {total_players}")
                    col3.metric("📥 Total Answers Processed", len(df))
                    
                    st.divider()
                    st.subheader("🚀 Live Player Progress")
                    
                    # Format data for visual columns
                    admin_board['Points'] = admin_board['Points'].astype(int)
                    admin_board['Questions_Answered'] = admin_board['Questions_Answered'].astype(int)
                    
                    # Upgraded Dataframe with visual progress bars
                    st.dataframe(
                        admin_board, 
                        hide_index=True, 
                        use_container_width=True,
                        column_config={
                            "Who": st.column_config.TextColumn(
                                "Player Name", 
                                width="medium"
                            ),
                            "Questions_Answered": st.column_config.ProgressColumn(
                                "Quiz Progress",
                                help="How many questions they have answered",
                                format="%d / 10",
                                min_value=0,
                                max_value=TOTAL_Q,
                                width="large"
                            ),
                            "Points": st.column_config.NumberColumn(
                                "Current Score",
                                format="%d pts",
                                width="small"
                            )
                        }
                    )
                    
                    st.divider()
                    st.subheader("📈 Live Scoreboard Race")
                    
                    # Live bar chart
                    chart_data = admin_board.set_index("Who")["Points"]
                    st.bar_chart(chart_data, color="#FFD700")

                else:
                    st.info("No one has submitted an answer yet. Waiting for players to join the fray...")
            else:
                st.error("Failed to connect to the database.")
        except Exception as e:
            st.error(f"Error loading dashboard: {e}")

# --- SCREEN 3: ACTIVE QUIZ ---
elif st.session_state.current_q_index < len(questions_list):
    st.title("🏆 SCT and RIA team Trivia")
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

# --- SCREEN 4: END GAME / LEADERBOARD ---
else:
    st.title("🏆 SCT and RIA team Trivia")
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
                    
                    # 1. CRITICAL FIX: Force points to be numbers BEFORE doing any math
                    df['Points'] = pd.to_numeric(df['Points'], errors='coerce').fillna(0)
                    
                    # Calculate Leaderboard
                    leaderboard = df.groupby("Who")["Points"].sum().reset_index()
                    leaderboard = leaderboard.sort_values(by="Points", ascending=False).reset_index(drop=True)
                    
                    # 2. CRITICAL FIX: Use 'dense' ranking. 
                    # If scores are 8, 8, 7 -> Ranks will be 1, 1, 2 (No medals are skipped!)
                    leaderboard['RankNum'] = leaderboard['Points'].rank(method='dense', ascending=False).astype(int)
                    
                    # 3. Add Medals based on true rank
                    def get_medal(rank):
                        if rank == 1: return "🥇 1"
                        elif rank == 2: return "🥈 2"
                        elif rank == 3: return "🥉 3"
                        else: return str(rank)
                        
                    leaderboard['Rank'] = leaderboard['RankNum'].apply(get_medal)
                    leaderboard['Points'] = leaderboard['Points'].astype(int)
                    
                    # Announce Champion(s) with CSS Animation
                    if not leaderboard.empty:
                        # Grab the absolute highest score on the board
                        max_score = int(leaderboard['Points'].max())
                        
                        # Find EVERYONE who has that exact score
                        winners_df = leaderboard[leaderboard['Points'] == max_score]
                        winners_list = winners_df['Who'].tolist()
                        
                        if len(winners_list) > 1:
                            # It's a tie! 
                            winners_str = " & ".join(winners_list)
                            st.markdown(f"<div class='champion-text'>🏆 TIE: {winners_str} Win ({max_score} pts)! 🏆</div>", unsafe_allow_html=True)
                        else:
                            # Solo winner
                            winner = winners_list[0]
                            st.markdown(f"<div class='champion-text'>🏆 {winner} Wins ({max_score} pts)! 🏆</div>", unsafe_allow_html=True)
                    
                    # Display beautiful dataframe without the default Pandas index
                    display_df = leaderboard[['Rank', 'Who', 'Points']]
                    
                    st.dataframe(
                        display_df, 
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
