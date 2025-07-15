
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

st.title("🎯 Number Draw Simulation Tool")

with st.form("sim_form"):
    entry_fee = st.number_input("Entry Fee (₹)", value=20)
    payout1 = st.number_input("1 Match Payout (₹)", value=25)
    payout2 = st.number_input("2 Match Payout (₹)", value=200)
    payout3 = st.number_input("3 Match Payout (₹)", value=250)
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
