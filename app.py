# --- Importy ---
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px

# --- Stałe ---
GRAMS_IN_TROY_OUNCE = 31.1034768

# --- Funkcje pomocnicze ---

def load_prices():
    try:
        df = pd.read_csv("lbma_data.csv", parse_dates=["Date"], sep=None, engine='python')
    except FileNotFoundError:
        st.sidebar.error("Brak pliku `lbma_data.csv` na serwerze. Proszę dodać ten plik.")
        st.stop()
    except Exception as e:
        st.sidebar.error(f"Błąd przy czytaniu pliku `lbma_data.csv`: {e}")
        st.stop()

    rename_map = {
        "Gold_EUR": "Gold",
        "Silver_EUR": "Silver",
        "Platinum_EUR": "Platinum",
        "Palladium_EUR": "Palladium"
    }
    required_columns = {"Date", "Gold_EUR", "Silver_EUR", "Platinum_EUR", "Palladium_EUR"}
    if not required_columns.issubset(df.columns):
        st.sidebar.error("Plik `lbma_data.csv` musi zawierać kolumny: Date, Gold_EUR, Silver_EUR, Platinum_EUR, Palladium_EUR.")
        st.stop()

    df = df.rename(columns=rename_map)
    df = df.set_index("Date")
    if df.isnull().any().any():
        df = df.fillna(method='ffill')
    return df

def get_next_available_price(prices, date):
    date = pd.to_datetime(date)
    future_dates = prices.index[prices.index >= date]
    return prices.loc[future_dates[0]] if not future_dates.empty else prices.iloc[-1]

def simulate_fixed_strategy(
    amount, start_date, end_date, frequency, tranche_amount,
    prices, gold_markup, silver_markup, platinum_markup, palladium_markup,
    gold_pct=40, silver_pct=30, platinum_pct=15, palladium_pct=15
):
    freq_map = {
        "Jednorazowa": None, "Tygodniowa": "W", "Miesięczna": "M",
        "Kwartalna": "Q", "Roczna": "A",
        "One-time": None, "Weekly": "W", "Monthly": "M", "Quarterly": "Q", "Annual": "A"
    }
    
    if freq_map[frequency] is None:
        schedule = pd.DatetimeIndex([pd.to_datetime(start_date)])
    else:
        schedule = pd.date_range(start=start_date, end=end_date, freq=freq_map[frequency])

    portfolio = pd.DataFrame(index=schedule, columns=["Gold_g", "Silver_g", "Platinum_g", "Palladium_g", "Investment_EUR"]).fillna(0.0)
    
    for i, date in enumerate(schedule):
        price_row = get_next_available_price(prices, date)
        if price_row is None:
            continue

        gold_price_g = price_row["Gold"] / GRAMS_IN_TROY_OUNCE
        silver_price_g = price_row["Silver"] / GRAMS_IN_TROY_OUNCE
        platinum_price_g = price_row["Platinum"] / GRAMS_IN_TROY_OUNCE
        palladium_price_g = price_row["Palladium"] / GRAMS_IN_TROY_OUNCE

        gold_price_buy = gold_price_g * (1 + gold_markup / 100)
        silver_price_buy = silver_price_g * (1 + silver_markup / 100)
        platinum_price_buy = platinum_price_g * (1 + platinum_markup / 100)
        palladium_price_buy = palladium_price_g * (1 + palladium_markup / 100)

        tranche = amount if i == 0 else tranche_amount

        portfolio.loc[date, "Gold_g"] = (tranche * (gold_pct/100)) / gold_price_buy
        portfolio.loc[date, "Silver_g"] = (tranche * (silver_pct/100)) / silver_price_buy
        portfolio.loc[date, "Platinum_g"] = (tranche * (platinum_pct/100)) / platinum_price_buy
        portfolio.loc[date, "Palladium_g"] = (tranche * (palladium_pct/100)) / palladium_price_buy
        portfolio.loc[date, "Investment_EUR"] = tranche

    portfolio_cumsum = portfolio.cumsum()
    return portfolio_cumsum

def map_prices_to_portfolio(prices, portfolio_index):
    available_dates = prices.index
    mapped_dates = []
    for d in portfolio_index:
        if d in available_dates:
            mapped_dates.append(d)
        else:
            future_dates = available_dates[available_dates >= d]
            if not future_dates.empty:
                mapped_dates.append(future_dates[0])
            else:
                mapped_dates.append(available_dates[-1])
    prices_now = prices.loc[mapped_dates]
    prices_now.index = portfolio_index
    return prices_now

# --- Główna aplikacja ---

st.set_page_config(page_title="Strategia FIXED – Majątek w Metalach", page_icon="💰", layout="wide")

st.title("📈 Strategia FIXED: Pierwszy zakup + Systematyczne dokupy")

# Wybór języka
language = st.sidebar.selectbox("Wybierz język / Choose language", ("Polski", "English"))

# Ładowanie danych
prices = load_prices()

# Parametry wejściowe
today = datetime.date.today()
min_date, max_date = prices.index.min().date(), prices.index.max().date()
if today > max_date:
    today = max_date

if language == "Polski":
    st.sidebar.header("Parametry Inwestycji")
    amount = st.sidebar.number_input("Kwota Początkowa (EUR)", min_value=1000.0, step=1000.0, value=100000.0)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.sidebar.date_input("Data Startu", value=today - datetime.timedelta(days=5*365), min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.sidebar.date_input("Data Końca", value=today, min_value=min_date, max_value=max_date)

    frequency = st.sidebar.selectbox("Częstotliwość Zakupów", ["Jednorazowa", "Tygodniowa", "Miesięczna", "Kwartalna", "Roczna"])
    tranche_amount = st.sidebar.number_input("Kwota Transzy (EUR)", min_value=0.0, step=100.0, value=1000.0)

    st.sidebar.header("Marże Zakupowe (%)")
    gold_markup = st.sidebar.number_input("Złoto", 0.0, 50.0, 9.9)
    silver_markup = st.sidebar.number_input("Srebro", 0.0, 50.0, 13.5)
    platinum_markup = st.sidebar.number_input("Platyna", 0.0, 50.0, 14.3)
    palladium_markup = st.sidebar.number_input("Pallad", 0.0, 50.0, 16.9)

    st.sidebar.header("Proporcje Metali (%)")
else:
    st.sidebar.header("Investment Parameters")
    amount = st.sidebar.number_input("Initial Amount (EUR)", min_value=1000.0, step=1000.0, value=100000.0)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.sidebar.date_input("Start Date", value=today - datetime.timedelta(days=5*365), min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.sidebar.date_input("End Date", value=today, min_value=min_date, max_value=max_date)

    frequency = st.sidebar.selectbox("Purchase Frequency", ["One-time", "Weekly", "Monthly", "Quarterly", "Annual"])
    tranche_amount = st.sidebar.number_input("Tranche Amount (EUR)", min_value=0.0, step=100.0, value=1000.0)

    st.sidebar.header("Purchase Margins (%)")
    gold_markup = st.sidebar.number_input("Gold", 0.0, 50.0, 9.9)
    silver_markup = st.sidebar.number_input("Silver", 0.0, 50.0, 13.5)
    platinum_markup = st.sidebar.number_input("Platinum", 0.0, 50.0, 14.3)
    palladium_markup = st.sidebar.number_input("Palladium", 0.0, 50.0, 16.9)

    st.sidebar.header("Metal Proportions (%)")

# Suwaki proporcji
gold_pct = st.sidebar.slider("Gold (%)", 0, 100, 40, step=5)
silver_pct = st.sidebar.slider("Silver (%)", 0, 100, 30, step=5)
platinum_pct = st.sidebar.slider("Platinum (%)", 0, 100, 15, step=5)
palladium_pct = st.sidebar.slider("Palladium (%)", 0, 100, 15, step=5)

sum_pct = gold_pct + silver_pct + platinum_pct + palladium_pct
if sum_pct == 100:
    st.sidebar.success(f"✅ Sum: {sum_pct}%")
else:
    st.sidebar.error(f"❌ Sum: {sum_pct}% (Must be 100%)")

# Symulacja
if st.sidebar.button("Symuluj Strategię FIXED") and sum_pct == 100:
    with st.spinner("Symuluję strategię..."):
        portfolio_cumsum = simulate_fixed_strategy(
            amount, start_date, end_date, frequency, tranche_amount,
            prices, gold_markup, silver_markup, platinum_markup, palladium_markup,
            gold_pct, silver_pct, platinum_pct, palladium_pct
        )

        prices_now = map_prices_to_portfolio(prices, portfolio_cumsum.index)
        valuation = (
            portfolio_cumsum["Gold_g"] * prices_now["Gold"] / GRAMS_IN_TROY_OUNCE +
            portfolio_cumsum["Silver_g"] * prices_now["Silver"] / GRAMS_IN_TROY_OUNCE +
            portfolio_cumsum["Platinum_g"] * prices_now["Platinum"] / GRAMS_IN_TROY_OUNCE +
            portfolio_cumsum["Palladium_g"] * prices_now["Palladium"] / GRAMS_IN_TROY_OUNCE
        )

        total_invested = portfolio_cumsum["Investment_EUR"].iloc[-1]
        final_value = valuation.iloc[-1]
        performance = ((final_value / total_invested) - 1) * 100

        # Wyniki
        st.header("📊 Wyniki Strategii")
        c1, c2, c3 = st.columns(3)
        c1.metric("💶 Zainwestowano łącznie", f"{total_invested:,.2f} EUR")
        c2.metric("📈 Wartość Portfela", f"{final_value:,.2f} EUR")
        c3.metric("📊 Wynik Inwestycyjny", f"{performance:.2f}%")

        st.subheader("📈 Wartość Portfela w Czasie")
        fig = px.line(x=portfolio_cumsum.index, y=valuation, labels={'x':'Data', 'y':'Wartość Portfela (EUR)'})
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Szczegóły Inwestycji")
        st.dataframe(portfolio_cumsum.round(2))
