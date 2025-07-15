
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

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

def simulate(entry_fee, payout1, payout2, payout3, num_players, num_rounds):
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
            net = reward - entry_fee
            profits[i] += net
            round_profit += net
        round_summary.append({
            "Round": rnd,
            "Total Spent": num_players * entry_fee,
            "Total Payout": round_profit + (num_players * entry_fee),
            "Net House Profit": -round_profit
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

# Preset payout schemes
presets = {
    "Conservative": {"entry": 10, "p1": 10, "p2": 50, "p3": 100},
    "Balanced": {"entry": 20, "p1": 25, "p2": 200, "p3": 250},
    "Aggressive": {"entry": 50, "p1": 100, "p2": 1000, "p3": 2000}
}

st.title("🎯 Number Draw Simulation Tool")

# Show probabilities
with st.expander("ℹ️ Match Probability Reference"):
    probs = calculate_probabilities()
    st.write(pd.DataFrame(probs.items(), columns=["Match Count", "Probability"]))

# Admin preset selector
st.sidebar.header("🛠 Admin Configuration")
preset_name = st.sidebar.selectbox("Choose Payout Preset", list(presets.keys()))
preset = presets[preset_name]

st.sidebar.markdown("**Selected Preset Values:**")
st.sidebar.write(f"Entry Fee: ₹{preset['entry']}")
st.sidebar.write(f"1 Match Payout: ₹{preset['p1']}")
st.sidebar.write(f"2 Match Payout: ₹{preset['p2']}")
st.sidebar.write(f"3 Match Payout: ₹{preset['p3']}")

with st.form("sim_form"):
    entry_fee = st.number_input("Entry Fee (₹)", value=preset['entry'])
    payout1 = st.number_input("1 Match Payout (₹)", value=preset['p1'])
    payout2 = st.number_input("2 Match Payout (₹)", value=preset['p2'])
    payout3 = st.number_input("3 Match Payout (₹)", value=preset['p3'])
    num_players = st.number_input("Number of Players", value=1000)
    num_rounds = st.number_input("Number of Rounds", value=100)
    submitted = st.form_submit_button("Run Simulation")

if submitted:
    st.info("Running simulation... please wait ⏳")
    summary_df, profits_array, round_df = simulate(entry_fee, payout1, payout2, payout3, int(num_players), int(num_rounds))
    st.success("✅ Simulation complete!")
    st.subheader("📊 Summary")
    st.dataframe(summary_df)

    st.subheader("📈 Player Profit Distribution")
    import matplotlib.pyplot as plt
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
