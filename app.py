
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import json
import os

PRESET_FILE = "presets.json"

# Load presets
def load_presets():
    if os.path.exists(PRESET_FILE):
        with open(PRESET_FILE, "r") as f:
            return json.load(f)
    return {}

# Save updated presets
def save_presets(presets):
    with open(PRESET_FILE, "w") as f:
        json.dump(presets, f, indent=2)

# Calculate theoretical match probabilities
def calculate_probabilities():
    total_combinations = math.comb(100, 3)
    prob_0 = math.comb(91, 3) / total_combinations
    prob_1 = (math.comb(9, 1) * math.comb(91, 2)) / total_combinations
    prob_2 = (math.comb(9, 2) * math.comb(91, 1)) / total_combinations
    prob_3 = math.comb(9, 3) / total_combinations
    return {
        "0 Matches": round(prob_0, 5),
        "1 Match": round(prob_1, 5),
        "2 Matches": round(prob_2, 5),
        "3 Matches": round(prob_3, 5)
    }

# Simulation logic with optional bonus
def simulate(entry_fee, payout1, payout2, payout3, num_players, num_rounds, bonus=False):
    number_pool = np.arange(1, 101)
    payouts = {1: payout1, 2: payout2, 3: payout3}
    player_choices = [np.random.choice(number_pool, 3, replace=False) for _ in range(num_players)]
    profits = np.zeros(num_players)
    round_summary = []

    for rnd in range(1, num_rounds + 1):
        draw = np.random.choice(number_pool, 9, replace=False)
        round_profit = 0
        for i in range(num_players):
            match = len(set(player_choices[i]) & set(draw))
            reward = payouts.get(match, 0)
            if bonus and rnd % 5 == 0:  # Example bonus: every 5th round
                reward *= 1.2
            net = reward - entry_fee
            profits[i] += net
            round_profit += net
        round_summary.append({
            "Round": rnd,
            "Total Spent": num_players * entry_fee,
            "Total Payout": round_profit + (num_players * entry_fee),
            "Net House Profit": -round_profit,
            "House Edge (%)": round((-round_profit / (num_players * entry_fee)) * 100, 2)
        })

    summary = {
        "Total Rounds": num_rounds,
        "Players": num_players,
        "Total Spent (₹)": num_players * num_rounds * entry_fee,
        "Total Returned (₹)": round(profits.sum() + num_players * num_rounds * entry_fee, 2),
        "Net House Profit (₹)": round(-(profits.sum()), 2),
        "Avg Profit per Player (₹)": round(profits.mean(), 2),
        "Players in Profit": np.sum(profits > 0),
        "Players in Loss": np.sum(profits < 0),
        "Players Breakeven": np.sum(profits == 0)
    }

    return pd.DataFrame([summary]), profits, pd.DataFrame(round_summary)

# Streamlit App
st.title("🎯 Number Draw Simulation Tool")

with st.expander("ℹ️ Match Probability Reference"):
    st.write(pd.DataFrame(calculate_probabilities().items(), columns=["Match Count", "Probability"]))

presets = load_presets()

# Admin controls
st.sidebar.header("🛠 Admin Configuration")
selected = st.sidebar.selectbox("Choose Preset", list(presets.keys()))
preset = presets[selected]
st.sidebar.write(preset)

st.sidebar.subheader("💾 Create Custom Preset")
with st.sidebar.form("custom_preset_form"):
    new_name = st.text_input("Preset Name")
    new_entry = st.number_input("Entry Fee", min_value=1, value=20)
    new_p1 = st.number_input("1 Match Payout", min_value=0, value=25)
    new_p2 = st.number_input("2 Match Payout", min_value=0, value=200)
    new_p3 = st.number_input("3 Match Payout", min_value=0, value=250)
    save_it = st.form_submit_button("Save Preset")
    if save_it and new_name:
        presets[new_name] = {"entry": new_entry, "p1": new_p1, "p2": new_p2, "p3": new_p3}
        save_presets(presets)
        st.sidebar.success(f"Preset '{new_name}' saved!")

with st.form("sim_form"):
    tier = st.selectbox("Select Tier", ["Tier 1 (₹10)", "Tier 2 (₹50)", "Tier 3 (₹100)"])
    if tier == "Tier 1 (₹10)":
        entry_fee = 10
    elif tier == "Tier 2 (₹50)":
        entry_fee = 50
    else:
        entry_fee = 100

    payout1 = st.number_input("1 Match Payout", value=preset['p1'])
    payout2 = st.number_input("2 Match Payout", value=preset['p2'])
    payout3 = st.number_input("3 Match Payout", value=preset['p3'])
    num_players = st.number_input("Number of Players", value=1000)
    num_rounds = st.number_input("Number of Rounds", value=100)
    bonus_round = st.checkbox("Enable Bonus on every 5th round (+20%)")
    submitted = st.form_submit_button("Run Simulation")

if submitted:
    st.info("Running simulation... please wait ⏳")
    summary_df, profits_array, round_df = simulate(entry_fee, payout1, payout2, payout3, int(num_players), int(num_rounds), bonus_round)
    st.success("✅ Simulation complete!")
    st.subheader("📊 Summary")
    st.dataframe(summary_df)

    st.subheader("📈 Player Profit Distribution")
    fig, ax = plt.subplots()
    ax.hist(profits_array, bins=50, color='skyblue', edgecolor='black')
    ax.set_title("Player Profits Histogram")
    ax.set_xlabel("Net Profit (₹)")
    ax.set_ylabel("Number of Players")
    st.pyplot(fig)

    st.subheader("📉 Round-wise House Profit")
    st.line_chart(round_df.set_index("Round")["Net House Profit"])

    st.subheader("⬇ Download CSV")
    st.download_button("Download Summary", summary_df.to_csv(index=False), file_name="summary.csv")
    st.download_button("Download Round Breakdown", round_df.to_csv(index=False), file_name="rounds.csv")
