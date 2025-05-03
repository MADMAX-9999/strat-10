# Aplikacja Streamlit - Wersja 0.4
# Budowanie strategii inwestycyjnej w metale szlachetne z obsługą danych historycznych, inflacji i symulacji dla FIXED

import streamlit as st
import pandas as pd
import os

# Konfiguracja strony
st.set_page_config(page_title="Strategia Majątku w Metalach", page_icon="💰", layout="centered")

# Funkcja wyboru języka
def select_language():
    language = st.sidebar.selectbox("Wybierz język / Choose language", ("Polski", "English"))
    return language

# Funkcja wczytania danych cen metali
def load_metal_prices():
    try:
        prices = pd.read_csv("lbma_data.csv", parse_dates=["Date"])
        prices.set_index("Date", inplace=True)
        return prices
    except FileNotFoundError:
        st.error("Brak pliku lbma_data.csv. / Missing lbma_data.csv file.")
        return None

# Funkcja wczytania danych inflacyjnych
def load_inflation(language):
    if language == "Polski":
        filename = "inflacja-PL.csv"
    else:
        filename = "inflacja-EN.csv"
        if not os.path.isfile(filename):
            filename = "inflacja-PL.csv"  # Domyślnie PL jeśli brak EN
    try:
        inflation = pd.read_csv(filename, parse_dates=["Date"])
        inflation.set_index("Date", inplace=True)
        return inflation
    except FileNotFoundError:
        st.error("Brak pliku inflacyjnego. / Missing inflation data file.")
        return None

# Funkcja formularza podstawowych danych
def input_initial_data(language):
    if language == "Polski":
        st.sidebar.header("Dane podstawowe")
        amount = st.sidebar.number_input("Kwota początkowej alokacji (EUR)", min_value=0.0, step=100.0)
        start_date = st.sidebar.date_input("Data pierwszego zakupu")
        end_date = st.sidebar.date_input("Data ostatniego zakupu")
        st.sidebar.subheader("Zakupy systematyczne (transze odnawialne)")
        frequency = st.sidebar.selectbox("Periodyczność", ("Tygodniowa", "Miesięczna", "Kwartalna"))
        tranche_amount = st.sidebar.number_input("Kwota każdej transzy (EUR)", min_value=0.0, step=50.0)
    else:
        st.sidebar.header("Basic Information")
        amount = st.sidebar.number_input("Initial Allocation Amount (EUR)", min_value=0.0, step=100.0)
        start_date = st.sidebar.date_input("First Purchase Date")
        end_date = st.sidebar.date_input("Last Purchase Date")
        st.sidebar.subheader("Recurring Purchases (Renewable Tranches)")
        frequency = st.sidebar.selectbox("Frequency", ("Weekly", "Monthly", "Quarterly"))
        tranche_amount = st.sidebar.number_input("Amount of Each Tranche (EUR)", min_value=0.0, step=50.0)
    return amount, start_date, end_date, frequency, tranche_amount

# Funkcja wyboru strategii
def select_strategy(language):
    if language == "Polski":
        st.sidebar.header("Wybór strategii")
        strategy = st.sidebar.radio("Wybierz strategię", ("FIXED", "MOMENTUM", "VALUE"))
    else:
        st.sidebar.header("Strategy Selection")
        strategy = st.sidebar.radio("Choose a strategy", ("FIXED", "MOMENTUM", "VALUE"))
    return strategy

# Funkcja ustawienia proporcji dla FIXED
def fixed_allocation(language):
    st.subheader("Ustaw proporcje metali / Set metal proportions")
    gold = st.slider("Złoto / Gold (%)", 0, 100, 40)
    silver = st.slider("Srebro / Silver (%)", 0, 100, 30)
    platinum = st.slider("Platyna / Platinum (%)", 0, 100, 15)
    palladium = st.slider("Pallad / Palladium (%)", 0, 100, 15)
    total = gold + silver + platinum + palladium
    st.write(f"Suma procentów: {total}%")
    if total != 100:
        st.error("Suma procentów musi wynosić 100% / Total must be 100%!")
    return gold, silver, platinum, palladium

# Funkcja symulacji zakupów FIXED
def simulate_fixed_strategy(amount, start_date, end_date, frequency, tranche_amount, gold_pct, silver_pct, platinum_pct, palladium_pct, prices):
    freq_map = {"Tygodniowa": "W", "Miesięczna": "M", "Kwartalna": "Q", "Weekly": "W", "Monthly": "M", "Quarterly": "Q"}
    schedule = pd.date_range(start=start_date, end=end_date, freq=freq_map.get(frequency, "M"))
    portfolio = pd.DataFrame(index=schedule, columns=["Gold", "Silver", "Platinum", "Palladium"])
    portfolio = portfolio.fillna(0.0)

    for date in schedule:
        if date in prices.index:
            investment = tranche_amount
            portfolio.loc[date, "Gold"] = (investment * gold_pct / 100) / prices.loc[date, "Gold"]
            portfolio.loc[date, "Silver"] = (investment * silver_pct / 100) / prices.loc[date, "Silver"]
            portfolio.loc[date, "Platinum"] = (investment * platinum_pct / 100) / prices.loc[date, "Platinum"]
            portfolio.loc[date, "Palladium"] = (investment * palladium_pct / 100) / prices.loc[date, "Palladium"]
    portfolio_cumsum = portfolio.cumsum()
    return portfolio_cumsum

# Główne wywołanie aplikacji
def main():
    st.title("💼 Strategia Budowy Majątku w Metalach")
    st.write("Wprowadź dane w panelu bocznym i obserwuj wyniki tutaj.")

    language = select_language()
    amount, start_date, end_date, frequency, tranche_amount = input_initial_data(language)
    strategy = select_strategy(language)

    prices = load_metal_prices()
    inflation = load_inflation(language)

    if prices is not None and inflation is not None:
        st.header("Podsumowanie Wyborów / Summary")
        st.write(f"**Strategia / Strategy**: {strategy}")
        st.write(f"**Kwota początkowa / Initial Amount**: {amount} EUR")
        st.write(f"**Data pierwszego zakupu / First Purchase Date**: {start_date}")
        st.write(f"**Data ostatniego zakupu / Last Purchase Date**: {end_date}")
        st.write(f"**Periodyczność / Frequency**: {frequency}")
        st.write(f"**Kwota transzy / Tranche Amount**: {tranche_amount} EUR")

        if strategy == "FIXED":
            gold, silver, platinum, palladium = fixed_allocation(language)
            if gold + silver + platinum + palladium == 100:
                st.success("Strategia FIXED ustawiona poprawnie!")

                if st.button("Rozpocznij symulację / Start Simulation"):
                    portfolio = simulate_fixed_strategy(amount, start_date, end_date, frequency, tranche_amount, gold, silver, platinum, palladium, prices)
                    st.line_chart(portfolio)
                    st.success("Symulacja zakończona sukcesem!")

if __name__ == "__main__":
    main()
