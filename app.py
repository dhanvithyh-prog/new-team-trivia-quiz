import streamlit as st
import pandas as pd
import requests
import json
import time
import streamlit.components.v1 as components

# Using 'wide' layout helps the side-by-side dashboard look incredible on a laptop
st.set_page_config(page_title="SCT and RIA Teams Trivia", layout="wide")

# Securely grab database credentials from Streamlit Secrets
UPSTASH_URL = st.secrets["UPSTASH_URL"]
UPSTASH_TOKEN = st.secrets["UPSTASH_TOKEN"]
HEADERS = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

# --- TIMER CHANGED TO 1.5 MINUTES (90 SECONDS) ---
QUIZ_DURATION_SEC = 90  

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

# --- GLOBAL GAME STATE HELPERS ---
def get_global_state():
    try:
        res = requests.get(f"{UPSTASH_URL}/get/quiz_state", headers=HEADERS)
        if res.status_code == 200:
            val = res.json().get("result")
            if val:
                return json.loads(val)
    except Exception:
        pass
    return {"status": "waiting", "end_time": 0}

def set_global_state(status, duration_sec):
    end_time = time.time() + duration_sec if status == "active" else 0
    state = {"status": status, "end_time": end_time}
    requests.post(f"{UPSTASH_URL}/set/quiz_state", headers=HEADERS, data=json.dumps(state))

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
    /* Restrict width for players on wide layout so reading isn't exhausting */
    .stForm { max-width: 800px; margin: 0 auto; }
    </style>
""", unsafe_allow_html=True)


# --- SCREEN 1: LOGIN ---
if not st.session_state.player_name and not st.session_state.is_admin:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏆 SCT and RIA Teams Trivia")
        st.write("Welcome to the challenge! Enter your name to begin.")
        name_input = st.text_input("Your Name:")
        
        if st.button("Join Game", use_container_width=True):
            if name_input.strip() == "ADMIN_SCT":
                st.session_state.is_admin = True
                st.rerun()
            elif name_input.strip() != "":
                st.session_state.player_name = name_input.strip()
                st.rerun()
            else:
                st.warning("Please enter a valid name!")


# --- SCREEN 2: PRESENTER DASHBOARD (LAPTOP OPTIMIZED) ---
elif st.session_state.is_admin:
    st.title("🎛️ Presenter Command Center")
    global_state = get_global_state()
    
    with st.spinner("Fetching live server data..."):
        try:
            response = requests.get(f"{UPSTASH_URL}/lrange/trivia_answers/0/-1", headers=HEADERS)
            if response.status_code == 200:
                raw_data = response.json().get("result", [])
                
                # Pre-process data
                df = pd.DataFrame()
                if raw_data:
                    parsed_data = [json.loads(item) for item in raw_data]
                    df = pd.DataFrame(parsed_data)
                    df['Points'] = pd.to_numeric(df['Points'], errors='coerce').fillna(0)
                    
                    admin_board = df.groupby("Who").agg(
                        Points=('Points', 'sum'),
                        Questions_Answered=('Question', 'count')
                    ).reset_index().sort_values(by="Points", ascending=False)
                    
                    total_players = len(admin_board)
                    finished_players = len(admin_board[admin_board['Questions_Answered'] == TOTAL_Q])
                else:
                    admin_board = pd.DataFrame()
                    total_players = finished_players = 0
                
                total_answers = len(df)
                
                # --- ROW 1: METRICS ---
                m1, m2, m3 = st.columns(3)
                m1.metric("👥 Active Players", total_players)
                m2.metric("🏁 Completed Quiz", f"{finished_players} / {max(1, total_players)}")
                m3.metric("📥 Total Answers Processed", total_answers)
                
                st.divider()
                
                # --- ROW 2: MASTER CONTROLS ---
                c1, c2, c3 = st.columns(3)
                with c1:
                    if global_state["status"] == "waiting":
                        if st.button("🚀 RELEASE QUIZ (1.5 Min)", type="primary", use_container_width=True):
                            set_global_state("active", QUIZ_DURATION_SEC)
                            st.rerun()
                    else:
                        time_left = max(0, int(global_state["end_time"] - time.time()))
                        st.warning(f"⏳ ACTIVE ({time_left}s left)")
                        if st.button("🛑 STOP / PAUSE QUIZ", type="primary", use_container_width=True):
                            set_global_state("waiting", 0)
                            st.rerun()
                            
                with c2:
                    if st.button("🔄 Refresh Live Data", use_container_width=True):
                        st.rerun()
                        
                with c3:
                    if st.button("☢️ Nuke Database (Reset All)", type="secondary", use_container_width=True):
                        requests.get(f"{UPSTASH_URL}/del/trivia_answers", headers=HEADERS)
                        set_global_state("waiting", 0)
                        st.success("Database Wiped!")
                        time.sleep(1)
                        st.rerun()

                st.divider()

                # --- ROW 3: SIDE-BY-SIDE ANALYTICS (No Scrolling needed) ---
                col_chart, col_table = st.columns(2)
                
                with col_chart:
                    st.markdown("### 📊 Live Score Visualization")
                    if not admin_board.empty:
                        chart_data = admin_board[['Who', 'Points']].set_index('Who')
                        st.bar_chart(chart_data, color="#FFD700", height=300)
                    else:
                        st.info("Waiting for scores...")
                        
                with col_table:
                    st.markdown("### 🏃‍♂️ Detailed Player Tracking")
                    if not admin_board.empty:
                        admin_board['Points'] = admin_board['Points'].astype(int)
                        admin_board['Questions_Answered'] = admin_board['Questions_Answered'].astype(int)
                        
                        st.dataframe(
                            admin_board[['Who', 'Questions_Answered', 'Points']], 
                            hide_index=True, 
                            use_container_width=True,
                            height=300, # Keeps the table from pushing the screen down
                            column_config={
                                "Who": st.column_config.TextColumn("Player Name", width="small"),
                                "Questions_Answered": st.column_config.ProgressColumn("Quiz Progress", format="%d", min_value=0, max_value=TOTAL_Q),
                                "Points": st.column_config.NumberColumn("Score", format="%d pts", width="small")
                            }
                        )
                    else:
                        st.info("Waiting for data...")
                        
        except Exception as e:
            st.error(f"Error loading dashboard: {e}")


# --- MAIN PLAYER FLOW ---
else:
    global_state = get_global_state()
    
    # We restrict the width for the player view using columns so it doesn't stretch awkwardly on wide monitors
    _, player_col, _ = st.columns([1, 2, 1])
    
    with player_col:
        # --- SCREEN 1.5: WAITING ROOM ---
        if global_state["status"] == "waiting":
            st.title("🏆 SCT and RIA Teams Trivia")
            st.info("✋ **Waiting Room:** The host has not started the quiz yet.")
            st.write("When the presenter says go, click the button below to join the live session!")
            
            if st.button("🔄 Check if Game Started", type="primary", use_container_width=True):
                st.rerun()

        # --- SCREEN 3: ACTIVE QUIZ ---
        elif global_state["status"] == "active" and time.time() < global_state["end_time"] and st.session_state.current_q_index < len(questions_list):
            st.title("🏆 SCT and RIA Teams Trivia")
            
            # Inject Live HTML Ticking Timer Component
            end_time_ms = int(global_state["end_time"] * 1000)
            components.html(f"""
                <div id="timer" style="font-size: 20px; font-weight: bold; color: white; background-color: #E50914; text-align: center; font-family: sans-serif; padding: 10px; border-radius: 8px;">
                    Loading Time...
                </div>
                <script>
                var countDownDate = {end_time_ms};
                var x = setInterval(function() {{
                  var now = new Date().getTime();
                  var distance = countDownDate - now;
                  var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                  var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                  document.getElementById("timer").innerHTML = "⏳ " + minutes + "m " + seconds + "s Remaining";
                  if (distance < 0) {{
                    clearInterval(x);
                    document.getElementById("timer").innerHTML = "🚨 TIME IS UP! 🚨";
                  }}
                }}, 1000);
                </script>
            """, height=60)
            
            current_q = questions_list[st.session_state.current_q_index]
            options, correct_answer = quiz_data[current_q]
            
            st.write(f"👤 Playing as: **{st.session_state.player_name}** | Question {st.session_state.current_q_index + 1} of {len(questions_list)}")
            st.progress((st.session_state.current_q_index) / len(questions_list))
            st.divider()

            if not st.session_state.answered_current:
                with st.form(key=f"form_{current_q}"):
                    st.subheader(current_q)
                    choice = st.radio("Select your answer:", options, index=None)
                    submit = st.form_submit_button("Lock it in!", use_container_width=True)

                if submit:
                    # Backend Kill Switch
                    if time.time() > global_state["end_time"]:
                        st.error("🚨 BUZZER BEATER DENIED! Time expired.")
                        time.sleep(2)
                        st.rerun() 
                        
                    elif choice is None:
                        st.warning("Please select an answer before submitting!")
                    else:
                        is_correct = (choice == correct_answer)
                        payload = {"Who": st.session_state.player_name, "Question": current_q, "Answer": choice, "Points": 1 if is_correct else 0}
                        
                        with st.spinner("Recording answer..."):
                            try:
                                response = requests.post(f"{UPSTASH_URL}/lpush/trivia_answers", headers=HEADERS, data=json.dumps(payload))
                                if response.status_code == 200:
                                    st.session_state.answered_current = True
                                    st.session_state.last_was_correct = is_correct
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error saving answer: {e}")
                                
            else:
                st.subheader(current_q)
                if st.session_state.last_was_correct:
                    st.success(f"🎯 Correct! The answer was **{correct_answer}**.")
                else:
                    st.error(f"❌ Incorrect. The correct answer was **{correct_answer}**.")
                    
                if st.button("Next Question ➡️", type="primary", use_container_width=True):
                    st.session_state.current_q_index += 1
                    st.session_state.answered_current = False
                    st.rerun()

        # --- SCREEN 4: END GAME / LEADERBOARD (Or Time Expired) ---
        else:
            st.title("🏆 SCT and RIA Teams Trivia")
            
            if global_state["status"] == "active" and time.time() >= global_state["end_time"]:
                st.error("🚨 TIME IS UP! Pencils down. Here is how everyone did.")
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
                            df['Points'] = pd.to_numeric(df['Points'], errors='coerce').fillna(0)
                            
                            leaderboard = df.groupby("Who")["Points"].sum().reset_index()
                            leaderboard = leaderboard.sort_values(by="Points", ascending=False).reset_index(drop=True)
                            leaderboard['RankNum'] = leaderboard['Points'].rank(method='dense', ascending=False).astype(int)
                            
                            def get_medal(rank):
                                if rank == 1: return "🥇 1"
                                elif rank == 2: return "🥈 2"
                                elif rank == 3: return "🥉 3"
                                else: return str(rank)
                                
                            leaderboard['Rank'] = leaderboard['RankNum'].apply(get_medal)
                            leaderboard['Points'] = leaderboard['Points'].astype(int)
                            
                            if not leaderboard.empty:
                                max_score = int(leaderboard['Points'].max())
                                winners_df = leaderboard[leaderboard['Points'] == max_score]
                                winners_list = winners_df['Who'].tolist()
                                
                                if len(winners_list) > 1:
                                    winners_str = " & ".join(winners_list)
                                    st.markdown(f"<div class='champion-text'>🏆 TIE: {winners_str} Win ({max_score} pts)! 🏆</div>", unsafe_allow_html=True)
                                else:
                                    winner = winners_list[0]
                                    st.markdown(f"<div class='champion-text'>🏆 {winner} Wins ({max_score} pts)! 🏆</div>", unsafe_allow_html=True)
                            
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
                except Exception as e:
                    st.error(f"Couldn't load the leaderboard. Check your connection. {e}")
                    
            st.divider()
            if st.button("🔄 Refresh Leaderboard", use_container_width=True):
                st.rerun()
