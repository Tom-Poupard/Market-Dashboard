# ====================================================
# 1. Imports
# ====================================================
import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import date
import plotly.express as px

# ====================================================
# 2. Function Definitions
# ====================================================

def download_data(tickers, start_date=None, end_date=None):
    all_data = []
    valid_tickers = []
    failed_tickers = []

    for t in tickers:
        try:
            df = yf.download(t, start=start_date, end=end_date, progress=False)["Close"]
            if not df.empty:
                df.name = t
                all_data.append(df)
                valid_tickers.append(t)
            else:
                failed_tickers.append(t)
        except:
            failed_tickers.append(t)

    if all_data:
        data = pd.concat(all_data, axis=1)
        return data, valid_tickers, failed_tickers
    else:
        return pd.DataFrame(), [], failed_tickers

def preprocess(data):
    return data.ffill().dropna(how="all")

def normalize(prices):
    returns = prices.pct_change().fillna(0)
    cum_returns = (1 + returns).cumprod()
    return cum_returns

def plot(data, title):
    df = data.reset_index().melt(id_vars="Date", var_name="Ticker", value_name="Price")
    fig = px.line(
        df,
        x="Date",
        y="Price",
        color="Ticker",
        title=title,
        template="plotly_dark",
        hover_data={"Price": ":.2f", "Date": True, "Ticker": True},
    )
    fig.update_layout(
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        font=dict(color="white"),
        title=dict(x=0.5),
        hoverlabel=dict(bgcolor="rgba(30,30,30,0.8)", font_size=12),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    fig.update_traces(line=dict(width=1.2))
    return fig

def create_dashboard(data, title):
    if data.empty:
        st.error("No valid data available to display.")
        return

    min_date = data.index.min().date()
    max_date = data.index.max().date()

    # Sidebar filter pour les tickers
    cols = st.sidebar.multiselect(
        "Select assets to display:",
        options=data.columns.tolist(),
        default=data.columns.tolist()
    )

    date_range = st.sidebar.date_input("Date range", [min_date, max_date])
    if len(date_range) == 2:
        start, end = date_range
    else:
        start, end = min_date, max_date

    mask = (data.index.date >= start) & (data.index.date <= end)
    data_filtered = data.loc[mask, cols]

    if data_filtered.empty:
        st.warning("No data available for the selected range or assets.")
        return

    fig = plot(normalize(data_filtered), title)
    st.title(title)
    st.plotly_chart(fig, use_container_width=True)

# ====================================================
# 3. Main Workflow
# ====================================================

# Mapping des classes d'actifs et leurs tickers
asset_classes = {
    "Cross Asset": ["SPY", "IEF", "GLD", "USO", "UUP", "WEAT"],
    "Equity": ["SPY", "QQQ", "IWM"],
    "Bonds": ["IEF", "TLT", "SHY"],
    "Forex": ["UUP", "FXE", "FXY"],
    "Rates": ["^IRX", "^TNX", "^TYX"]  # ex: 3M, 10Y, 30Y US Treasury yields
}

asset_names = {
    "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq 100 ETF",
    "IWM": "Russell 2000 ETF",
    "IEF": "10-Year Treasury ETF",
    "TLT": "20+ Year Treasury ETF",
    "SHY": "1-3 Year Treasury ETF",
    "GLD": "Gold ETF",
    "USO": "Crude Oil ETF",
    "UUP": "US Dollar Index ETF",
    "WEAT": "Wheat ETF",
    "FXE": "Euro ETF",
    "FXY": "Yen ETF",
    "^IRX": "3M Treasury Yield",
    "^TNX": "10Y Treasury Yield",
    "^TYX": "30Y Treasury Yield"
}

start_date = "1980-01-01"
end_date = date.today().strftime("%Y-%m-%d")

# --- Sidebar pour choisir la classe d'actifs ---
st.sidebar.header("📊 Asset Class")
selected_class = st.sidebar.radio(
    "Choose asset class:",
    list(asset_classes.keys())
)

# --- Télécharger et afficher les données pour la classe choisie ---
tickers = asset_classes[selected_class]
data, valid_tickers, failed_tickers = download_data(tickers, start_date, end_date)
if data.empty:
    st.error(f"No valid data for {selected_class}.")
else:
    data.columns = [asset_names.get(t, t) for t in valid_tickers]
    data = preprocess(data)
    cum_returns = normalize(data)
    create_dashboard(cum_returns, f"📊 {selected_class} Dashboard")
