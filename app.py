import streamlit as st
import numpy as np
import pandas as pd

def simulate(entry_fee, payout1, payout2, payout3, num_players, num_rounds):
    number_pool = np.arange(1, 101)
    payouts = {1: payout1, 2: payout2, 3: payout3}
    player_choices = [np.random.choice(number_pool, 3, replace=False) for _ in range(num_players)]
    profits = np.zeros(num_players)

    for _ in range(num_rounds):
        draw = np.random.choice(number_pool, 9, replace=False)
        for i in range(num_players):
            match = len(set(player_choices[i]) & set(draw))
            reward = payouts.get(match, 0)
            profits[i] += reward - entry_fee

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

    return pd.DataFrame([summary])

st.title("🎯 Number Draw Simulation Tool")

with st.form("sim_form"):
    entry_fee = st.number_input("Entry Fee (₹)", value=20)
    payout1 = st.number_input("1 Match Payout (₹)", value=25)
    payout2 = st.number_input("2 Match Payout (₹)", value=200)
    payout3 = st.number_input("3 Match Payout (₹)", value=250)
    num_players = st.number_input("Number of Players", value=1000)
    num_rounds = st.number_input("Number of Rounds", value=1000)
    submitted = st.form_submit_button("Run Simulation")

if submitted:
    st.info("Running simulation... please wait ⏳")
    df = simulate(entry_fee, payout1, payout2, payout3, int(num_players), int(num_rounds))
    st.success("✅ Simulation complete!")
    st.dataframe(df)
    st.download_button("Download Results as CSV", df.to_csv(index=False), file_name="simulation_results.csv")
