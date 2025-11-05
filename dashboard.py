# ====================================================
# Python Dashboard - Cross-Asset Market Monitor
# ====================================================

# ====================================================
# 1. Imports
# ====================================================
import os
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import streamlit as st
from datetime import date, timedelta

# ====================================================
# 2. Functions
# ====================================================

# 2.1 Load or Update Data
def update_data(tickers, file="data.csv"):
    """
    Charge les données depuis CSV si existant,
    sinon télécharge depuis Yahoo Finance.
    Met à jour uniquement les nouvelles données si nécessaires.
    """
    if os.path.exists(file):
        data = pd.read_csv(file, index_col=0, parse_dates=True)
        last_date = data.index.max().date()
        today = pd.to_datetime("today").date()
        if last_date < today:
            new_data = yf.download(
                tickers,
                start=last_date + timedelta(days=1),
                end=today,
                auto_adjust=True,
                progress=False
            )["Close"]
            if not new_data.empty:
                data = pd.concat([data, new_data])
                data.to_csv(file)
                print(f"Données mises à jour jusqu'à {today}")
            else:
                print("Pas de nouvelles données disponibles")
        else:
            print("Les données sont déjà à jour")
    else:
        data = yf.download(tickers, auto_adjust=True, progress=False)["Close"]
        data.to_csv(file)
        print("Données téléchargées depuis Yahoo Finance")
    return data

# 2.2 Preprocessing Data
def preprocess(data):
    data = data.ffill().dropna()
    return data

# 2.3 Normalizing Data
def normalize(prices):
    returns = prices.pct_change().fillna(0)
    cum_returns = (1 + returns).cumprod()
    return cum_returns

# 2.4 Plotting
def plot(data, title):
    fig = plt.figure(figsize=(10, 5))
    for col in data.columns:
        plt.plot(data[col], label=col)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.grid()
    return fig

# 2.5 Streamlit Dashboard
def create_dashboard(data, title=None):
    st.set_page_config(page_title=title, layout="wide")
    st.title(title)

    # Sidebar - Sélection des colonnes
    cols = st.sidebar.multiselect(
        "Select columns",
        options=data.columns,
        default=data.columns
    )

    # Sidebar - Sélection des dates
    min_date = data.index.min().date()
    max_date = data.index.max().date()
    start, end = st.sidebar.date_input("Date range", [min_date, max_date])
    if not isinstance(start, date):
        start, end = start[0], start[1]

    mask = (data.index.date >= start) & (data.index.date <= end)
    data_filtered = data.loc[mask, cols]

    # Affichage graphique
    fig = plot(normalize(data_filtered), title)
    st.pyplot(fig)

# ====================================================
# 3. Main Workflow
# ====================================================

# Liste des tickers
tickers = ["ES=F", "ZN=F", "GC=F", "CL=F", "DX=F", "ZW=F"]

ticker_names = {
    "ES=F": "S&P 500 Futures",
    "ZN=F": "10-Year Treasury Note Futures",
    "GC=F": "Gold Futures",
    "CL=F": "Crude Oil Futures",
    "DX=F": "US Dollar Index Futures",
    "ZW=F": "Wheat Futures"
}

readable_tickers = [ticker_names[t] for t in tickers]

# Chargement ou mise à jour des données
start_date = "1980-01-01"
end_date = date.today().strftime("%Y-%m-%d")

data = update_data(tickers, "data.csv")
data.columns = readable_tickers
data = preprocess(data)
cum_returns = normalize(data)

# Button to manually update the data from the dashboard
if st.button("Actualiser les données"):
    data = update_data(tickers, "data.csv")
    data.columns = readable_tickers
    data = preprocess(data)
    cum_returns = normalize(data)
    st.success("Données mises à jour !")

# Création du dashboard
title = "Cross-Asset Market Monitor"
create_dashboard(cum_returns, title)
