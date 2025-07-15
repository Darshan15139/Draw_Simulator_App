# app.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import json
import os
import random

PRESET_FILE = "presets.json"

# Load presets from file
def load_presets():
    if os.path.exists(PRESET_FILE):
        with open(PRESET_FILE, "r") as f:
            return json.load(f)
    return {}

# Save presets to file
def save_presets(presets):
    with open(PRESET_FILE, "w") as f:
        json.dump(presets, f, indent=2)

# Match probabilities for reference
def calculate_probabilities():
    total_combinations = math.comb(100, 3)
    return {
        "0 Matches": round(math.comb(91, 3) / total_combinations, 5),
        "1 Match": round((math.comb(9, 1) * math.comb(91, 2)) / total_combinations, 5),
        "2 Matches": round((math.comb(9, 2) * math.comb(91, 1)) / total_combinations, 5),
        "3 Matches": round(math.comb(9, 3) / total_combinations, 5)
    }

# Player strategy pickers
def pick_numbers(strategy, pool, recent_draws=None):
    if strategy == "fixed":
        return pool[:3]
    elif strategy == "rotate":
        return random.sample(pool, 3)
    elif strategy == "adaptive" and recent_draws:
        avoid = set().union(*recent_draws)
        available = [n for n in range(1, 101) if n not in avoid]
        return random.sample(available, 3)
    elif strategy == "pattern":
        return [random.randint(1, 33), random.randint(34, 66), random.randint(67, 100)]
    else:
        return random.sample(range(1, 101), 3)

# Simulate with player types and adaptive logic
def simulate(entry_fee, payout1, payout2, payout3, num_players, num_rounds, bonus, strategy_dist, adaptive_memory):
    payouts = {1: payout1, 2: payout2, 3: payout3}
    number_pool = np.arange(1, 101)
    strategies = []
    player_pools = []
    recent_draws = []

    for strategy, pct in strategy_dist.items():
        count = int(num_players * pct / 100)
        for _ in range(count):
            strategies.append(strategy)
            if strategy == "fixed":
                player_pools.append(random.sample(range(1, 101), 3))
            elif strategy == "rotate":
                player_pools.append(random.sample(range(1, 101), 10))
            else:
                player_pools.append([])

    profits = np.zeros(num_players)
    strategy_profit = {k: [] for k in strategy_dist.keys()}
    round_summary = []

    for rnd in range(1, num_rounds + 1):
        draw = random.sample(range(1, 101), 9)
        recent_draws.append(draw)
        if len(recent_draws) > adaptive_memory:
            recent_draws.pop(0)

        round_profit = 0
        for i in range(num_players):
            picks = pick_numbers(strategies[i], player_pools[i], recent_draws)
            match = len(set(picks) & set(draw))
            reward = payouts.get(match, 0)
            if bonus and rnd % 5 == 0:
                reward *= 1.2
            net = reward - entry_fee
            profits[i] += net
            strategy_profit[strategies[i]].append(net)
            round_profit += net

        round_summary.append({
            "Round": rnd,
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
        "Expected Value per Ticket (₹)": round((calculate_probabilities()["1 Match"] * payout1 + calculate_probabilities()["2 Matches"] * payout2 + calculate_probabilities()["3 Matches"] * payout3) - entry_fee, 2),
        "Actual Avg Return per Ticket (₹)": round(profits.sum() / (num_players * num_rounds), 2),
    }
    for k in strategy_profit:
        summary[f"Avg Profit - {k}"] = round(np.mean(strategy_profit[k]), 2) if strategy_profit[k] else 0

    return pd.DataFrame([summary]), profits, pd.DataFrame(round_summary)

# Streamlit UI
st.title("🎯 Number Draw Simulator with Strategy Behaviors")

with st.expander("ℹ️ Match Probability Reference"):
    st.write(pd.DataFrame(calculate_probabilities().items(), columns=["Match Count", "Probability"]))

presets = load_presets()
selected = st.sidebar.selectbox("Choose Preset", list(presets.keys()))
preset = presets[selected]

st.sidebar.subheader("🧠 Player Strategy Distribution (%)")
strategy_dist = {
    "fixed": st.sidebar.slider("Fixed", 0, 100, 20),
    "rotate": st.sidebar.slider("Rotate", 0, 100, 20),
    "adaptive": st.sidebar.slider("Adaptive", 0, 100, 20),
    "random": st.sidebar.slider("Random", 0, 100, 20),
    "pattern": st.sidebar.slider("Pattern", 0, 100, 20)
}
total_pct = sum(strategy_dist.values())

if total_pct != 100:
    st.sidebar.error("Strategy percentages must sum to 100%")

adaptive_memory = st.sidebar.number_input("Adaptive Memory (Rounds)", min_value=1, max_value=20, value=5)

with st.form("sim_form"):
    entry_fee = st.number_input("Entry Fee (₹)", value=preset['entry'])
    payout1 = st.number_input("1 Match Payout (₹)", value=preset['p1'])
    payout2 = st.number_input("2 Match Payout (₹)", value=preset['p2'])
    payout3 = st.number_input("3 Match Payout (₹)", value=preset['p3'])
    num_players = st.number_input("Number of Players", value=1000)
    num_rounds = st.number_input("Number of Rounds", value=100)
    bonus = st.checkbox("Enable 20% Bonus every 5th round")
    submitted = st.form_submit_button("Run Simulation")

if submitted and total_pct == 100:
    st.info("Running simulation... please wait ⏳")
    summary_df, profits_array, round_df = simulate(entry_fee, payout1, payout2, payout3, int(num_players), int(num_rounds), bonus, strategy_dist, adaptive_memory)
    st.success("✅ Simulation complete!")

    st.subheader("📊 Simulation Summary")
    st.dataframe(summary_df)

    st.subheader("📈 Player Profit Distribution")
    fig, ax = plt.subplots()
    ax.hist(profits_array, bins=50, color='skyblue', edgecolor='black')
    ax.set_title("Player Profits Histogram")
    ax.set_xlabel("Net Profit (₹)")
    ax.set_ylabel("Number of Players")
    st.pyplot(fig)

    st.subheader("📉 Round-wise House Edge (%)")
    st.line_chart(round_df.set_index("Round")["House Edge (%)"])

    st.subheader("⬇ Download Results")
    st.download_button("Download Summary", summary_df.to_csv(index=False), file_name="summary.csv")
    st.download_button("Download Round Breakdown", round_df.to_csv(index=False), file_name="rounds.csv")
