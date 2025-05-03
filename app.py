import streamlit as st
import pandas as pd
import os
import datetime

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
            filename = "inflacja-PL.csv"
    try:
        try:
            inflation = pd.read_csv(filename, encoding='utf-8')
        except UnicodeDecodeError:
            inflation = pd.read_csv(filename, encoding='cp1250')
        if inflation.columns[0] != "Date":
            inflation.rename(columns={inflation.columns[0]: "Date"}, inplace=True)
        inflation["Date"] = pd.to_datetime(inflation["Date"], errors='coerce')
        inflation.set_index("Date", inplace=True)
        return inflation
    except FileNotFoundError:
        st.error("Brak pliku inflacyjnego. / Missing inflation data file.")
        return None

# Funkcja formularza danych podstawowych
def input_initial_data(prices, language):
    min_date = prices.index.min().date()
    max_date = prices.index.max().date()
    today = datetime.date.today()
    end_default = today if today <= max_date else max_date
    start_default = end_default - datetime.timedelta(days=365*20)
    if start_default < min_date:
        start_default = min_date

    if language == "Polski":
        st.sidebar.header("Dane podstawowe")
        amount = st.sidebar.number_input("Kwota początkowej alokacji (EUR)", min_value=0.0, step=100.0, value=100000.0)
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Data pierwszego zakupu", value=start_default, min_value=min_date, max_value=max_date)
        with col2:
            end_date = st.date_input("Data ostatniego zakupu", value=end_default, min_value=min_date, max_value=max_date)
        st.sidebar.subheader("Zakupy systematyczne (transze odnawialne)")
        frequency = st.sidebar.selectbox("Periodyczność", ("Tygodniowa", "Miesięczna", "Kwartalna"))
    else:
        st.sidebar.header("Basic Information")
        amount = st.sidebar.number_input("Initial Allocation Amount (EUR)", min_value=0.0, step=100.0, value=100000.0)
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("First Purchase Date", value=start_default, min_value=min_date, max_value=max_date)
        with col2:
            end_date = st.date_input("Last Purchase Date", value=end_default, min_value=min_date, max_value=max_date)
        st.sidebar.subheader("Recurring Purchases (Renewable Tranches)")
        frequency = st.sidebar.selectbox("Frequency", ("Weekly", "Monthly", "Quarterly"))

    # Koszty zakupu
    st.sidebar.header("Koszt zakupu metali (%)")
    gold_markup = st.sidebar.number_input("Złoto (Gold) %", min_value=0.0, max_value=100.0, value=9.90, step=0.1)
    silver_markup = st.sidebar.number_input("Srebro (Silver) %", min_value=0.0, max_value=100.0, value=13.5, step=0.1)
    platinum_markup = st.sidebar.number_input("Platyna (Platinum) %", min_value=0.0, max_value=100.0, value=14.3, step=0.1)
    palladium_markup = st.sidebar.number_input("Pallad (Palladium) %", min_value=0.0, max_value=100.0, value=16.9, step=0.1)

    default_tranche = 250.0 if frequency in ["Tygodniowa", "Weekly"] else 1000.0 if frequency in ["Miesięczna", "Monthly"] else 3250.0
    tranche_amount = st.sidebar.number_input("Kwota każdej transzy (EUR)" if language == "Polski" else "Amount of Each Tranche (EUR)", min_value=0.0, step=50.0, value=default_tranche)

    return amount, start_date, end_date, frequency, tranche_amount, gold_markup, silver_markup, platinum_markup, palladium_markup

# Funkcja wyboru strategii
def select_strategy(language):
    if language == "Polski":
        st.sidebar.header("Wybór strategii")
        strategy = st.sidebar.radio("Wybierz strategię", ("FIXED", "MOMENTUM", "VALUE"))
    else:
        st.sidebar.header("Strategy Selection")
        strategy = st.sidebar.radio("Choose a strategy", ("FIXED", "MOMENTUM", "VALUE"))
    return strategy

# Funkcja ustawienia proporcji FIXED
def fixed_allocation(language):
    st.subheader("Ustaw proporcje metali / Set metal proportions")
    gold = st.slider("Złoto / Gold (%)", 0, 100, 40, step=5)
    silver = st.slider("Srebro / Silver (%)", 0, 100, 30, step=5)
    platinum = st.slider("Platyna / Platinum (%)", 0, 100, 15, step=5)
    palladium = st.slider("Pallad / Palladium (%)", 0, 100, 15, step=5)

    total = gold + silver + platinum + palladium
    st.write(f"**Suma:** {total}%")

    if total != 100:
        st.error("Suma musi wynosić dokładnie 100%! Proszę dostosować suwaki.")
    else:
        st.success("Suma wynosi 100%! Możesz kontynuować.")

    return gold, silver, platinum, palladium

# Funkcja symulacji FIXED
def simulate_fixed_strategy(amount, start_date, end_date, frequency, tranche_amount,
                             gold_pct, silver_pct, platinum_pct, palladium_pct,
                             prices, gold_markup, silver_markup, platinum_markup, palladium_markup):
    freq_map = {"Tygodniowa": "W", "Miesięczna": "M", "Kwartalna": "Q", "Weekly": "W", "Monthly": "M", "Quarterly": "Q"}
    schedule = pd.date_range(start=start_date, end=end_date, freq=freq_map.get(frequency, "M"))
    portfolio = pd.DataFrame(index=schedule, columns=["Gold", "Silver", "Platinum", "Palladium"])
    portfolio = portfolio.fillna(0.0)

    for date in schedule:
        if date in prices.index:
            price_gold_g = prices.loc[date, "Gold"] / 31.1034768
            price_silver_g = prices.loc[date, "Silver"] / 31.1034768
            price_platinum_g = prices.loc[date, "Platinum"] / 31.1034768
            price_palladium_g = prices.loc[date, "Palladium"] / 31.1034768

            # Ceny z marżą
            price_gold_g_buy = price_gold_g * (1 + gold_markup/100)
            price_silver_g_buy = price_silver_g * (1 + silver_markup/100)
            price_platinum_g_buy = price_platinum_g * (1 + platinum_markup/100)
            price_palladium_g_buy = price_palladium_g * (1 + palladium_markup/100)

            investment = tranche_amount

            portfolio.loc[date, "Gold"] = (investment * gold_pct / 100) / price_gold_g_buy
            portfolio.loc[date, "Silver"] = (investment * silver_pct / 100) / price_silver_g_buy
            portfolio.loc[date, "Platinum"] = (investment * platinum_pct / 100) / price_platinum_g_buy
            portfolio.loc[date, "Palladium"] = (investment * palladium_pct / 100) / price_palladium_g_buy

    portfolio_cumsum = portfolio.cumsum()
    return portfolio_cumsum

# Funkcja przeliczenia wartości depozytu wg spot
def calculate_portfolio_value_spot(portfolio, prices):
    common_dates = portfolio.index.intersection(prices.index)
    prices_g = prices.loc[common_dates] / 31.1034768
    value = (portfolio.loc[common_dates]["Gold"] * prices_g["Gold"] +
             portfolio.loc[common_dates]["Silver"] * prices_g["Silver"] +
             portfolio.loc[common_dates]["Platinum"] * prices_g["Platinum"] +
             portfolio.loc[common_dates]["Palladium"] * prices_g["Palladium"])
    return value

# Główne wywołanie aplikacji
def main():
    st.title("💼 Strategia Budowy Majątku w Metalach")
    st.write("Wprowadź dane w panelu bocznym i obserwuj wyniki tutaj.")

    language = select_language()
    prices = load_metal_prices()
    inflation = load_inflation(language)

    if prices is not None and inflation is not None:
        amount, start_date, end_date, frequency, tranche_amount, gold_markup, silver_markup, platinum_markup, palladium_markup = input_initial_data(prices, language)
        strategy = select_strategy(language)

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
                    portfolio = simulate_fixed_strategy(amount, start_date, end_date, frequency, tranche_amount,
                                                        gold, silver, platinum, palladium,
                                                        prices, gold_markup, silver_markup, platinum_markup, palladium_markup)

                    if not portfolio.empty:
                        st.subheader("Zakupione ilości metali (gramy)")
                        st.line_chart(portfolio.fillna(0))

                        portfolio_value_spot = calculate_portfolio_value_spot(portfolio, prices)
                        st.subheader("Wartość depozytu wg cen spot (EUR)")
                        st.line_chart(portfolio_value_spot.fillna(0))

                        st.success("Symulacja zakończona sukcesem!")
                    else:
                        st.error("Brak danych w wybranym zakresie dat! Proszę zmienić daty.")

if __name__ == "__main__":
    main()
