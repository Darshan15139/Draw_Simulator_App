
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

# Simulate with player types, adaptive logic, and draw mode
def simulate(entry_fee, payout1, payout2, payout3, num_players, num_rounds,
             bonus, strategy_dist, adaptive_memory, weighted_draw):
    payouts = {1: payout1, 2: payout2, 3: payout3}
    strategies = []
    player_pools = []
    recent_draws = []

    # Assign strategies and pools
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
        # Weighted or random draw
        if weighted_draw:
            weights = [2 if 1 <= i <= 20 else 1 for i in range(1, 101)]
            draw = random.choices(range(1, 101), weights=weights, k=9)
            draw = list(dict.fromkeys(draw))
            while len(draw) < 9:
                candidates = [i for i in range(1, 101) if i not in draw]
                draw.append(random.choice(candidates))
        else:
            draw = random.sample(range(1, 101), 9)

        recent_draws.append(draw)
        if len(recent_draws) > adaptive_memory:
            recent_draws.pop(0)

        round_profit = 0
        for i in range(num_players):
            picks = pick_numbers(strategies[i], player_pools[i], recent_draws)
            match_count = len(set(picks) & set(draw))
            reward = payouts.get(match_count, 0)
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

    # Build summary
    base_summary = {
        "Total Rounds": num_rounds,
        "Players": num_players,
        "Total Spent (₹)": num_players * num_rounds * entry_fee,
        "Total Returned (₹)": round(profits.sum() + num_players * num_rounds * entry_fee, 2),
        "Net House Profit (₹)": round(-(profits.sum()), 2),
        "Avg Profit per Player (₹)": round(profits.mean(), 2),
        "Expected Value per Ticket (₹)": round(
            (calculate_probabilities()["1 Match"] * payout1 +
             calculate_probabilities()["2 Matches"] * payout2 +
             calculate_probabilities()["3 Matches"] * payout3) - entry_fee, 2),
        "Actual Avg Return per Ticket (₹)": round(profits.sum() / (num_players * num_rounds), 2),
    }
    for strat, plist in strategy_profit.items():
        base_summary[f"Avg Profit - {strat}"] = round(np.mean(plist), 2) if plist else 0

    return pd.DataFrame([base_summary]), profits, pd.DataFrame(round_summary)

# Streamlit UI
st.title("🎯 Number Draw Simulator with Strategy Behaviors & Weighted Draw")

with st.expander("ℹ️ Match Probability Reference"):
    st.write(pd.DataFrame(calculate_probabilities().items(), columns=["Match Count", "Probability"]))

# Load and select presets
presets = load_presets()
selected_preset = st.sidebar.selectbox("Choose Preset", list(presets.keys()))
preset = presets[selected_preset]

# Strategy distribution sliders
st.sidebar.subheader("🧠 Player Strategy Distribution (%)")
strategy_dist = {
    "fixed": st.sidebar.slider("Fixed", 0, 100, 20),
    "rotate": st.sidebar.slider("Rotate", 0, 100, 20),
    "adaptive": st.sidebar.slider("Adaptive", 0, 100, 20),
    "random": st.sidebar.slider("Random", 0, 100, 20),
    "pattern": st.sidebar.slider("Pattern", 0, 100, 20)
}
if sum(strategy_dist.values()) != 100:
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
    weighted_draw = st.checkbox("Use Weighted/Favoured Draw (1-20 double weight)")
    col1, col2 = st.columns(2)
    run = col1.form_submit_button("Run Simulation")
    save_preset = col2.form_submit_button("💾 Save As Preset")

# Save preset
if save_preset:
    preset_name = st.text_input("Enter name for new preset", key="new_preset")
    if preset_name:
        presets[preset_name] = {"entry": entry_fee, "p1": payout1, "p2": payout2, "p3": payout3}
        save_presets(presets)
        st.toast(f"Preset '{preset_name}' saved.", icon="💾")

# Run simulation
if run and sum(strategy_dist.values()) == 100:
    st.info("Running simulation... please wait ⏳")
    summary_rand, profits_rand, rounds_rand = simulate(
        entry_fee, payout1, payout2, payout3,
        num_players, num_rounds, bonus,
        strategy_dist, adaptive_memory, False)
    if weighted_draw:
        summary_wt, profits_wt, rounds_wt = simulate(
            entry_fee, payout1, payout2, payout3,
            num_players, num_rounds, bonus,
            strategy_dist, adaptive_memory, True)
    st.success("✅ Simulation complete!")

    # Summary comparison
    st.subheader("📊 Summary Comparison")
    if weighted_draw:
        comp = pd.concat([
            summary_rand.assign(Mode="Random"),
            summary_wt.assign(Mode="Weighted")
        ])
        st.dataframe(comp)
        st.subheader("⚖️ EV vs Actual Return vs House Edge")
        comp_chart = comp.set_index("Mode")[
            ["Expected Value per Ticket (₹)", "Actual Avg Return per Ticket (₹)", "Net House Profit (₹)"]]
        st.bar_chart(comp_chart)
    else:
        st.dataframe(summary_rand)

    # Profit distribution
    st.subheader("📈 Player Profit Distribution (Random)")
    fig1, ax1 = plt.subplots()
    ax1.hist(profits_rand, bins=50, edgecolor='black')
    st.pyplot(fig1)
    if weighted_draw:
        st.subheader("📈 Player Profit Distribution (Weighted)")
        fig2, ax2 = plt.subplots()
        ax2.hist(profits_wt, bins=50, edgecolor='black')
        st.pyplot(fig2)

    # House edge over rounds
    st.subheader("📉 Round-wise House Edge (%)")
    st.line_chart(rounds_rand.set_index("Round")["House Edge (%)"])
    if weighted_draw:
        st.line_chart(rounds_wt.set_index("Round")["House Edge (%)"])

    # Download buttons
    st.subheader("⬇ Download CSVs")
    st.download_button("Download Random Summary", summary_rand.to_csv(index=False), file_name="random_summary.csv")
    if weighted_draw:
        st.download_button("Download Weighted Summary", summary_wt.to_csv(index=False), file_name="weighted_summary.csv")
        st.download_button("Download Random Rounds", rounds_rand.to_csv(index=False), file_name="random_rounds.csv")
        st.download_button("Download Weighted Rounds", rounds_wt.to_csv(index=False), file_name="weighted_rounds.csv")
