# Aplikacja Streamlit - Wersja 0.1
# Budowanie strategii inwestycyjnej w metale szlachetne

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
        st.header("Dane podstawowe")
        amount = st.number_input("Kwota początkowej alokacji (EUR)", min_value=0.0, step=100.0)
        start_date = st.date_input("Data pierwszego zakupu")
        end_date = st.date_input("Data ostatniego zakupu")
        st.subheader("Zakupy systematyczne (transze odnawialne)")
        frequency = st.selectbox("Periodyczność", ("Tygodniowa", "Miesięczna", "Kwartalna"))
        tranche_amount = st.number_input("Kwota każdej transzy (EUR)", min_value=0.0, step=50.0)
    else:
        st.header("Basic Information")
        amount = st.number_input("Initial Allocation Amount (EUR)", min_value=0.0, step=100.0)
        start_date = st.date_input("First Purchase Date")
        end_date = st.date_input("Last Purchase Date")
        st.subheader("Recurring Purchases (Renewable Tranches)")
        frequency = st.selectbox("Frequency", ("Weekly", "Monthly", "Quarterly"))
        tranche_amount = st.number_input("Amount of Each Tranche (EUR)", min_value=0.0, step=50.0)
    return amount, start_date, end_date, frequency, tranche_amount

# Funkcja wyboru strategii
def select_strategy(language):
    if language == "Polski":
        st.header("Wybór strategii")
        strategy = st.radio("Wybierz strategię", ("FIXED", "MOMENTUM", "VALUE"))
    else:
        st.header("Strategy Selection")
        strategy = st.radio("Choose a strategy", ("FIXED", "MOMENTUM", "VALUE"))
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
    language = select_language()
    amount, start_date, end_date, frequency, tranche_amount = input_initial_data(language)
    strategy = select_strategy(language)

    if strategy == "FIXED":
        gold, silver, platinum, palladium = fixed_allocation(language)
        if gold + silver + platinum + palladium == 100:
            st.success("Strategia FIXED ustawiona poprawnie!")

    if st.button("Dalej / Next"):
        st.info(f"Wybrano strategię: {strategy}")
        st.info(f"Kwota początkowa: {amount} EUR | Transze: {frequency} po {tranche_amount} EUR")

if __name__ == "__main__":
    main()
