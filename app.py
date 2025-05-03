# --- Importy ---
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px

# --- Konfiguracja strony ---
st.set_page_config(
    page_title="Strategia Majątku w Metalach",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Stałe ---
GRAMS_IN_TROY_OUNCE = 31.1034768

# --- Funkcje pomocnicze ---

def create_sample_lbma_data():
    start = datetime.date(2000, 1, 1)
    today = datetime.date.today()
    dates = pd.date_range(start=start, end=today, freq='B')
    np.random.seed(42)
    data = {
        'Date': dates,
        'Gold': 1200 + np.random.normal(0, 2, len(dates)).cumsum(),
        'Silver': 20 + np.random.normal(0, 0.1, len(dates)).cumsum(),
        'Platinum': 900 + np.random.normal(0, 2, len(dates)).cumsum(),
        'Palladium': 1500 + np.random.normal(0, 3, len(dates)).cumsum()
    }
    df = pd.DataFrame(data).clip(lower=0)
    return df

def load_prices():
    uploaded = st.sidebar.file_uploader("Upload LBMA CSV", type=['csv'])
    if uploaded:
        df = pd.read_csv(uploaded, parse_dates=["Date"])
    else:
        try:
            df = pd.read_csv("lbma_data.csv", parse_dates=["Date"])
        except:
            st.sidebar.info("Using sample LBMA data.")
            df = create_sample_lbma_data()
    df = df.set_index("Date")
    return df

def get_next_available_price(prices, date):
    date = pd.to_datetime(date)
    if date in prices.index:
        return prices.loc[date]
    future_dates = prices.index[prices.index >= date]
    return prices.loc[future_dates[0]] if not future_dates.empty else prices.iloc[-1]

def input_form(prices):
    st.sidebar.header("Parametry Inwestycji")
    min_date, max_date = prices.index.min().date(), prices.index.max().date()
    today = datetime.date.today()
    amount = st.sidebar.number_input("Kwota Początkowa (EUR)", min_value=1000.0, step=1000.0, value=100000.0)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.sidebar.date_input("Data Startu", value=today - datetime.timedelta(days=365*5), min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.sidebar.date_input("Data Końca", value=today, min_value=min_date, max_value=max_date)
    frequency = st.sidebar.selectbox("Częstotliwość Zakupów", ["Jednorazowa", "Tygodniowa", "Miesięczna", "Kwartalna", "Roczna"])
    tranche_amount = st.sidebar.number_input("Kwota Transzy (EUR)", min_value=0.0, step=100.0, value=1000.0)
    st.sidebar.header("Marże Zakupowe (%)")
    gold_markup = st.sidebar.number_input("Złoto", 0.0, 50.0, 9.9)
    silver_markup = st.sidebar.number_input("Srebro", 0.0, 50.0, 13.5)
    platinum_markup = st.sidebar.number_input("Platyna", 0.0, 50.0, 14.3)
    palladium_markup = st.sidebar.number_input("Pallad", 0.0, 50.0, 16.9)
    return amount, start_date, end_date, frequency, tranche_amount, gold_markup, silver_markup, platinum_markup, palladium_markup

def simulate_fixed(amount, start_date, end_date, frequency, tranche_amount, prices, markups):
    freq_map = {"Jednorazowa": None, "Tygodniowa": "W", "Miesięczna": "M", "Kwartalna": "Q", "Roczna": "A"}
    if freq_map.get(frequency) is None:
        schedule = pd.DatetimeIndex([pd.to_datetime(start_date)])
    else:
        schedule = pd.date_range(start=start_date, end=end_date, freq=freq_map[frequency])

    portfolio = pd.DataFrame(index=schedule, columns=["Gold", "Silver", "Platinum", "Palladium", "Investment"]).fillna(0.0)

    for i, date in enumerate(schedule):
        row = get_next_available_price(prices, date)
        if row is not None:
            price_gold = row["Gold"] / GRAMS_IN_TROY_OUNCE * (1 + markups['gold']/100)
            price_silver = row["Silver"] / GRAMS_IN_TROY_OUNCE * (1 + markups['silver']/100)
            price_platinum = row["Platinum"] / GRAMS_IN_TROY_OUNCE * (1 + markups['platinum']/100)
            price_palladium = row["Palladium"] / GRAMS_IN_TROY_OUNCE * (1 + markups['palladium']/100)
            tranche = amount if i == 0 else tranche_amount
            portfolio.loc[date, "Gold"] = (tranche * 0.4) / price_gold
            portfolio.loc[date, "Silver"] = (tranche * 0.3) / price_silver
            portfolio.loc[date, "Platinum"] = (tranche * 0.15) / price_platinum
            portfolio.loc[date, "Palladium"] = (tranche * 0.15) / price_palladium
            portfolio.loc[date, "Investment"] = tranche
    return portfolio.cumsum()

def simulate_dynamic(amount, start_date, end_date, frequency, tranche_amount, prices, markups):
    freq_map = {"Jednorazowa": None, "Tygodniowa": "W", "Miesięczna": "M", "Kwartalna": "Q", "Roczna": "A"}
    if freq_map.get(frequency) is None:
        schedule = pd.DatetimeIndex([pd.to_datetime(start_date)])
    else:
        schedule = pd.date_range(start=start_date, end=end_date, freq=freq_map[frequency])

    portfolio = pd.DataFrame(index=schedule, columns=["Gold", "Silver", "Platinum", "Palladium", "Investment"]).fillna(0.0)

    moving_avg = prices.rolling(window=252).mean()
    for i, date in enumerate(schedule):
        row = get_next_available_price(prices, date)
        avg_row = get_next_available_price(moving_avg, date)
        if row is not None and avg_row is not None:
            gold_under = row["Gold"] < avg_row["Gold"]
            silver_under = row["Silver"] < avg_row["Silver"]
            platinum_under = row["Platinum"] < avg_row["Platinum"]
            palladium_under = row["Palladium"] < avg_row["Palladium"]

            weights = {
                "Gold": 0.4 + 0.1 if gold_under else 0.4 - 0.1,
                "Silver": 0.3 + 0.1 if silver_under else 0.3 - 0.1,
                "Platinum": 0.15 + 0.05 if platinum_under else 0.15 - 0.05,
                "Palladium": 0.15 + 0.05 if palladium_under else 0.15 - 0.05,
            }
            total_weight = sum(weights.values())
            for key in weights:
                weights[key] /= total_weight

            price_gold = row["Gold"] / GRAMS_IN_TROY_OUNCE * (1 + markups['gold']/100)
            price_silver = row["Silver"] / GRAMS_IN_TROY_OUNCE * (1 + markups['silver']/100)
            price_platinum = row["Platinum"] / GRAMS_IN_TROY_OUNCE * (1 + markups['platinum']/100)
            price_palladium = row["Palladium"] / GRAMS_IN_TROY_OUNCE * (1 + markups['palladium']/100)
            tranche = amount if i == 0 else tranche_amount

            portfolio.loc[date, "Gold"] = (tranche * weights["Gold"]) / price_gold
            portfolio.loc[date, "Silver"] = (tranche * weights["Silver"]) / price_silver
            portfolio.loc[date, "Platinum"] = (tranche * weights["Platinum"]) / price_platinum
            portfolio.loc[date, "Palladium"] = (tranche * weights["Palladium"]) / price_palladium
            portfolio.loc[date, "Investment"] = tranche
    return portfolio.cumsum()

# --- Główna aplikacja ---

# Wczytaj dane
prices = load_prices()

# Wprowadź parametry
amount, start_date, end_date, frequency, tranche_amount, gold_markup, silver_markup, platinum_markup, palladium_markup = input_form(prices)

# Wybór strategii
strategy = st.sidebar.radio("Strategia", ["FIXED", "DYNAMIC"])

# Przycisk startu
if st.sidebar.button("Symuluj Strategię"):
    markups = {'gold': gold_markup, 'silver': silver_markup, 'platinum': platinum_markup, 'palladium': palladium_markup}
    
    if strategy == "FIXED":
        result = simulate_fixed(amount, start_date, end_date, frequency, tranche_amount, prices, markups)
    else:
        result = simulate_dynamic(amount, start_date, end_date, frequency, tranche_amount, prices, markups)

    # --- Obliczenia wartości portfela ---
    st.header("📈 Wyniki Strategii")
    
    prices_now = prices.loc[result.index]
    valuation = (
        result["Gold"] * prices_now["Gold"] / GRAMS_IN_TROY_OUNCE +
        result["Silver"] * prices_now["Silver"] / GRAMS_IN_TROY_OUNCE +
        result["Platinum"] * prices_now["Platinum"] / GRAMS_IN_TROY_OUNCE +
        result["Palladium"] * prices_now["Palladium"] / GRAMS_IN_TROY_OUNCE
    )

    total_invested = result["Investment"].iloc[-1]
    final_valuation = valuation.iloc[-1]
    performance = ((final_valuation / total_invested) - 1) * 100

    # --- Karty wynikowe ---
    col1, col2, col3 = st.columns(3)
    col1.metric("💶 Zainwestowano łącznie", f"{total_invested:,.2f} EUR")
    col2.metric("📊 Aktualna wartość portfela", f"{final_valuation:,.2f} EUR")
    col3.metric("📈 Wynik inwestycyjny", f"{performance:.2f}%")

    # --- Wykres wartości portfela ---
    st.subheader("📈 Wartość Portfela w Czasie")
    fig = px.line(
        x=result.index, y=valuation,
        labels={'x': 'Data', 'y': 'Wartość Portfela (EUR)'},
        title="Wartość Portfela"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Wykres udziału metali ---
    st.subheader("🥇 Udziały Metali na Koniec")
    last = result.iloc[-1][["Gold", "Silver", "Platinum", "Palladium"]]
    metal_labels = ["Złoto", "Srebro", "Platyna", "Pallad"]
    fig2 = px.pie(
        values=last.values, names=metal_labels,
        title="Udziały Metali (%)",
        hole=0.4
    )
    st.plotly_chart(fig2, use_container_width=True)

    # --- Tabela wyników ---
    st.subheader("📋 Szczegóły inwestycji (cumulative)")
    st.dataframe(result.round(2))
