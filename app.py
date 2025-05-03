# Aplikacja Streamlit - Wersja 0.2
# Budowanie strategii inwestycyjnej w metale szlachetne - poprawiona wersja: Sidebar na dane wejściowe

import streamlit as st

# Konfiguracja strony
st.set_page_config(page_title="Strategia Majątku w Metalach", page_icon="💰", layout="centered")

# Funkcja wyboru języka
def select_language():
    language = st.sidebar.selectbox("Wybierz język / Choose language", ("Polski", "English"))
    return language

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
    st.subheader("Ustaw proporcje metali")
    gold = st.slider("Złoto / Gold (%)", 0, 100, 40)
    silver = st.slider("Srebro / Silver (%)", 0, 100, 30)
    platinum = st.slider("Platyna / Platinum (%)", 0, 100, 15)
    palladium = st.slider("Pallad / Palladium (%)", 0, 100, 15)
    total = gold + silver + platinum + palladium
    st.write(f"Suma procentów: {total}%")
    if total != 100:
        st.error("Suma procentów musi wynosić 100% / Total must be 100%!")
    return gold, silver, platinum, palladium

# Główne wywołanie aplikacji
def main():
    st.title("💼 Strategia Budowy Majątku w Metalach")
    st.write("Wprowadź dane w panelu bocznym i obserwuj wyniki tutaj.")

    language = select_language()
    amount, start_date, end_date, frequency, tranche_amount = input_initial_data(language)
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

    if st.button("Dalej / Next"):
        st.info(f"Wybrano strategię: {strategy}")
        st.info(f"Kwota początkowa: {amount} EUR | Transze: {frequency} po {tranche_amount} EUR")

if __name__ == "__main__":
    main()
