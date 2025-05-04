import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Konfiguracja strony
st.set_page_config(page_title="Symulator Metali Szlachetnych", layout="wide")

# Wczytanie danych (Twoja funkcja load_data i load_inflation_data)
@st.cache_data
def load_data():
    df = pd.read_csv("lbma_data.csv", parse_dates=True, index_col=0)
    df = df.sort_index()
    df = df.dropna()
    return df

@st.cache_data
def load_inflation_data():
    df = pd.read_csv("inflacja.csv", sep=";", encoding="cp1250")
    df["Wartość"] = df["Wartość"].str.replace(",", ".").astype(float)
    df["Inflacja (%)"] = df["Wartość"] - 100
    return df[["Rok", "Inflacja (%)"]]

data = load_data()
inflation_real = load_inflation_data()

# Tłumaczenia i ustawienia języka (Twoja logika)

if "language" not in st.session_state:
    st.session_state.language = "Polski"

language_choice = st.selectbox(
    "🌐 Wybierz język / Sprache wählen",
    ("🇵🇱 Polski", "🇩🇪 Deutsch"),
    index=0 if st.session_state.language == "Polski" else 1
)

new_language = "Polski" if "Polski" in language_choice else "Deutsch"
if new_language != st.session_state.language:
    st.session_state.language = new_language
    st.experimental_rerun()

language = st.session_state.language

# ----------------------------------------
# 🌟 Główna część aplikacji – Expandery
# ----------------------------------------

st.title("Symulator ReBalancingu Portfela Metali Szlachetnych")
st.markdown("---")

# Parametry Symulacji
with st.expander("⚙️ Parametry Symulacji", expanded=True):
    today = datetime.today()
    default_initial_date = today.replace(year=today.year - 20)

    initial_allocation = st.number_input("💰 Kwota początkowej alokacji (EUR)", value=100000.0, step=100.0)

    initial_date = st.date_input(
        "📅 Data pierwszego zakupu",
        value=default_initial_date.date(),
        min_value=data.index.min().date(),
        max_value=data.index.max().date()
    )

    min_end_date = (pd.to_datetime(initial_date) + pd.DateOffset(years=7)).date()
    if min_end_date > data.index.max().date():
        min_end_date = data.index.max().date()

    end_purchase_date = st.date_input(
        "📅 Data ostatniego zakupu",
        value=data.index.max().date(),
        min_value=min_end_date,
        max_value=data.index.max().date()
    )

    days_difference = (pd.to_datetime(end_purchase_date) - pd.to_datetime(initial_date)).days
    years_difference = days_difference / 365.25

    if years_difference >= 7:
        st.success(f"✅ Zakres zakupów: {years_difference:.1f} lat.")
        dates_valid = True
    else:
        st.error(f"⚠️ Zakres zakupów: tylko {years_difference:.1f} lat. (minimum 7 lat wymagane!)")
        dates_valid = False

# Alokacja metali
with st.expander("⚖️ Alokacja metali szlachetnych (%)", expanded=True):
    if "alloc_Gold" not in st.session_state:
        st.session_state["alloc_Gold"] = 40
        st.session_state["alloc_Silver"] = 20
        st.session_state["alloc_Platinum"] = 20
        st.session_state["alloc_Palladium"] = 20

    if st.button("🔄 Resetuj do 40/20/20/20"):
        st.session_state["alloc_Gold"] = 40
        st.session_state["alloc_Silver"] = 20
        st.session_state["alloc_Platinum"] = 20
        st.session_state["alloc_Palladium"] = 20
        st.rerun()

    allocation_gold = st.slider("Złoto (Au)", 0, 100, st.session_state["alloc_Gold"])
    allocation_silver = st.slider("Srebro (Ag)", 0, 100, st.session_state["alloc_Silver"])
    allocation_platinum = st.slider("Platyna (Pt)", 0, 100, st.session_state["alloc_Platinum"])
    allocation_palladium = st.slider("Pallad (Pd)", 0, 100, st.session_state["alloc_Palladium"])

    total = allocation_gold + allocation_silver + allocation_platinum + allocation_palladium
    if total != 100:
        st.error(f"❗ Suma alokacji: {total}% – musi wynosić dokładnie 100%, aby kontynuować.")
        st.stop()

# Zakupy cykliczne
with st.expander("🔁 Zakupy cykliczne"):
    purchase_freq = st.selectbox("📈 Periodyczność zakupów", ["Brak", "Tydzień", "Miesiąc", "Kwartał"], index=1)
    if purchase_freq == "Tydzień":
        days_of_week = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]
        selected_day = st.selectbox("Dzień tygodnia zakupu", days_of_week, index=0)
        purchase_day = days_of_week.index(selected_day)
        default_purchase_amount = 250.0
    elif purchase_freq == "Miesiąc":
        purchase_day = st.number_input("Dzień miesiąca zakupu (1–28)", min_value=1, max_value=28, value=1)
        default_purchase_amount = 1000.0
    elif purchase_freq == "Kwartał":
        purchase_day = st.number_input("Dzień kwartału zakupu (1–28)", min_value=1, max_value=28, value=1)
        default_purchase_amount = 3250.0
    else:
        purchase_day = None
        default_purchase_amount = 0.0

    purchase_amount = st.number_input("Kwota dokupu (EUR)", value=default_purchase_amount, step=50.0)

# ReBalancing
with st.expander("♻️ ReBalancing"):
    rebalance_1 = st.checkbox("✅ ReBalancing 1", value=True)
    rebalance_1_condition = st.checkbox("⚡ Warunek odchylenia dla ReBalancing 1", value=False)
    rebalance_1_threshold = st.number_input("Próg odchylenia (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5)

    rebalance_2 = st.checkbox("✅ ReBalancing 2", value=False)
    rebalance_2_condition = st.checkbox("⚡ Warunek odchylenia dla ReBalancing 2", value=False)
    rebalance_2_threshold = st.number_input("Próg odchylenia (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5)

# Koszty magazynowania
with st.expander("📦 Koszty magazynowania"):
    storage_fee = st.number_input("Roczny koszt magazynowania (%)", value=1.5)
    vat = st.number_input("VAT (%)", value=19.0)
    storage_metal = st.selectbox("Metal do pokrycia kosztów", ["Gold", "Silver", "Platinum", "Palladium", "Best of year", "ALL"])

# Marże i prowizje
with st.expander("📊 Marże i prowizje"):
    margins = {
        "Gold": st.number_input("Marża Gold (%)", value=15.6),
        "Silver": st.number_input("Marża Silver (%)", value=18.36),
        "Platinum": st.number_input("Marża Platinum (%)", value=24.24),
        "Palladium": st.number_input("Marża Palladium (%)", value=22.49)
    }

# Ceny odkupu i ReBalancing
with st.expander("💵 Ceny odkupu i ReBalancing"):
    buyback_discounts = {
        "Gold": st.number_input("Złoto odk. od SPOT (%)", value=-1.5, step=0.1),
        "Silver": st.number_input("Srebro odk. od SPOT (%)", value=-3.0, step=0.1),
        "Platinum": st.number_input("Platyna odk. od SPOT (%)", value=-3.0, step=0.1),
        "Palladium": st.number_input("Pallad odk. od SPOT (%)", value=-3.0, step=0.1)
    }
    rebalance_markup = {
        "Gold": st.number_input("Złoto ReBalancing (%)", value=6.5, step=0.1),
        "Silver": st.number_input("Srebro ReBalancing (%)", value=6.5, step=0.1),
        "Platinum": st.number_input("Platyna ReBalancing (%)", value=6.5, step=0.1),
        "Palladium": st.number_input("Pallad ReBalancing (%)", value=6.5, step=0.1)
    }

# ----------------------------------------
# ➡️ Dalej uruchamiamy Twoją funkcję simulate(allocation)
# ➡️ Wyświetlamy wykresy i podsumowania
# ----------------------------------------

# =========================================
# 4. Główna sekcja aplikacji
# =========================================

st.title("Symulator ReBalancingu Portfela Metali Szlachetnych")
st.markdown("---")

result = simulate(allocation)

# === Korekta wartości portfela o realną inflację ===

# Słownik: Rok -> Inflacja
inflation_dict = dict(zip(inflation_real["Rok"], inflation_real["Inflacja (%)"]))

# Funkcja: obliczenie skumulowanej inflacji od startu
def calculate_cumulative_inflation(start_year, current_year):
    cumulative_factor = 1.0
    for year in range(start_year, current_year + 1):
        inflation = inflation_dict.get(year, 0.0) / 100  # Brak danych = 0% inflacji
        cumulative_factor *= (1 + inflation)
    return cumulative_factor

# Rok początkowy inwestycji
start_year = result.index.min().year

# Dodanie nowej kolumny z wartością realną portfela
real_values = []

for date in result.index:
    nominal_value = result.loc[date, "Portfolio Value"]
    current_year = date.year
    cumulative_inflation = calculate_cumulative_inflation(start_year, current_year)
    real_value = nominal_value / cumulative_inflation if cumulative_inflation != 0 else nominal_value
    real_values.append(real_value)

result["Portfolio Value Real"] = real_values

import matplotlib.pyplot as plt





# 📈 Wykres wartości portfela: nominalna vs realna vs inwestycje vs koszty magazynowania (Streamlit interaktywny)

# Przygotowanie danych do wykresu
result_plot = result.copy()
result_plot["Storage Cost"] = 0.0

# Oznaczenie kosztu magazynowania w odpowiednich dniach
storage_costs = result_plot[result_plot["Akcja"] == "storage_fee"].index
for d in storage_costs:
    result_plot.at[d, "Storage Cost"] = result_plot.at[d, "Invested"] * (storage_fee / 100) * (1 + vat / 100)

# ❗ Naprawiamy typ danych: wymuszamy float
for col in ["Portfolio Value", "Portfolio Value Real", "Invested", "Storage Cost"]:
    result_plot[col] = pd.to_numeric(result_plot[col], errors="coerce").fillna(0)

# Stworzenie DataFrame tylko z potrzebnymi seriami
chart_data = result_plot[["Portfolio Value", "Portfolio Value Real", "Invested", "Storage Cost"]]

# Nagłówki bardziej czytelne (opcjonalnie)
chart_data.rename(columns={
    "Portfolio Value": f"💰 {translations[language]['portfolio_value']}",
    "Portfolio Value Real": f"🏛️ {translations[language]['real_portfolio_value']}",
    "Invested": f"💵 {translations[language]['invested']}",
    "Storage Cost": f"📦 {translations[language]['storage_cost']}"
}, inplace=True)

# 📈 Ładny interaktywny wykres w Streamlit
st.subheader(translations[language]["chart_subtitle"])
st.line_chart(chart_data)


    
# Podsumowanie wyników

st.subheader(translations[language]["summary_title"])
start_date = result.index.min()
end_date = result.index.max()
years = (end_date - start_date).days / 365.25

alokacja_kapitalu = result["Invested"].max()
wartosc_metali = result["Portfolio Value"].iloc[-1]

if alokacja_kapitalu > 0 and years > 0:
    roczny_procent = (wartosc_metali / alokacja_kapitalu) ** (1 / years) - 1
else:
    roczny_procent = 0.0


st.subheader("📊 Wzrost cen metali od startu inwestycji")

start_date = result.index.min()
end_date = result.index.max()

start_prices = data.loc[start_date]
end_prices = data.loc[end_date]

metale = ["Gold", "Silver", "Platinum", "Palladium"]
wzrosty = {}

for metal in metale:
    start_price = start_prices[metal + "_EUR"]
    end_price = end_prices[metal + "_EUR"]
    wzrost = (end_price / start_price - 1) * 100
    wzrosty[metal] = wzrost

# Wyświetlenie ładnej tabelki
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Złoto (Au)", f"{wzrosty['Gold']:.2f}%")
with col2:
    st.metric("Srebro (Ag)", f"{wzrosty['Silver']:.2f}%")
with col3:
    st.metric("Platyna (Pt)", f"{wzrosty['Platinum']:.2f}%")
with col4:
    st.metric("Pallad (Pd)", f"{wzrosty['Palladium']:.2f}%")



st.subheader("⚖️ Aktualnie posiadane ilości metali (g)")

# Aktualne ilości gramów z ostatniego dnia
aktualne_ilosci = {
    "Gold": result.iloc[-1]["Gold"],
    "Silver": result.iloc[-1]["Silver"],
    "Platinum": result.iloc[-1]["Platinum"],
    "Palladium": result.iloc[-1]["Palladium"]
}

# Kolory metali: złoto, srebro, platyna, pallad
kolory_metali = {
    "Gold": "#D4AF37",      # złoto – kolor złoty
    "Silver": "#C0C0C0",    # srebro – kolor srebrny
    "Platinum": "#E5E4E2",  # platyna – bardzo jasny, biały odcień
    "Palladium": "#CED0DD"  # pallad – lekko niebieskawo-srebrny
}

# Wyświetlenie w czterech kolumnach z kolorowym napisem
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"<h4 style='color:{kolory_metali['Gold']}; text-align: center;'>Złoto (Au)</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci['Gold']:.2f} g")
with col2:
    st.markdown(f"<h4 style='color:{kolory_metali['Silver']}; text-align: center;'>Srebro (Ag)</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci['Silver']:.2f} g")
with col3:
    st.markdown(f"<h4 style='color:{kolory_metali['Platinum']}; text-align: center;'>Platyna (Pt)</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci['Platinum']:.2f} g")
with col4:
    st.markdown(f"<h4 style='color:{kolory_metali['Palladium']}; text-align: center;'>Pallad (Pd)</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci['Palladium']:.2f} g")

st.metric("💶 Alokacja kapitału", f"{alokacja_kapitalu:,.2f} EUR")
st.metric("📦 Wycena sprzedażowa metali", f"{wartosc_metali:,.2f} EUR")

# 🛒 Wartość zakupu metali dziś (uwzględniając aktualne ceny + marże)
metale = ["Gold", "Silver", "Platinum", "Palladium"]

# Ilość posiadanych gramów na dziś
ilosc_metali = {metal: result.iloc[-1][metal] for metal in metale}

# Aktualne ceny z marżą
aktualne_ceny_z_marza = {
    metal: data.loc[result.index[-1], metal + "_EUR"] * (1 + margins[metal] / 100)
    for metal in metale
}

# Wartość zakupu metali dzisiaj
wartosc_zakupu_metali = sum(
    ilosc_metali[metal] * aktualne_ceny_z_marza[metal]
    for metal in metale
)

# Wyświetlenie
st.metric("🛒 Wartość zakupowa metali", f"{wartosc_zakupu_metali:,.2f} EUR")

# 🧮 Opcjonalnie: różnica procentowa
if wartosc_zakupu_metali > 0:
    roznica_proc = ((wartosc_zakupu_metali / wartosc_metali) - 1) * 100
else:
    roznica_proc = 0.0

st.caption(f"📈 Różnica względem wartości portfela: {roznica_proc:+.2f}%")

st.subheader("📈 Średni roczny rozwój cen wszystkich metali razem (ważony alokacją)")

# Twoja alokacja początkowa w procentach (przypominam: allocation to słownik typu {"Gold": 0.4, "Silver": 0.2, itd.})

# Liczymy ważoną średnią cen startową i końcową
weighted_start_price = sum(
    allocation[metal] * data.loc[result.index.min()][metal + "_EUR"]
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]
)

weighted_end_price = sum(
    allocation[metal] * data.loc[result.index.max()][metal + "_EUR"]
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]
)

# Ilość lat inwestycji
start_date = result.index.min()
end_date = result.index.max()
years = (end_date - start_date).days / 365.25

# Ważony średnioroczny wzrost cen (CAGR)
if weighted_start_price > 0 and years > 0:
    weighted_avg_annual_growth = (weighted_end_price / weighted_start_price) ** (1 / years) - 1
else:
    weighted_avg_annual_growth = 0.0

# Wyświetlenie
st.metric("🌐 Średni roczny wzrost cen (ważony alokacją)", f"{weighted_avg_annual_growth * 100:.2f}%")



st.subheader("📅 Mały uproszczony podgląd: Pierwszy dzień każdego roku")

# Grupujemy po roku i bierzemy pierwszy dzień roboczy
result_filtered = result.groupby(result.index.year).first()

# Tworzymy prostą tabelę z wybranymi kolumnami
simple_table = pd.DataFrame({
    "Zainwestowane (EUR)": result_filtered["Invested"].round(0),
    "Wartość portfela (EUR)": result_filtered["Portfolio Value"].round(0),
    "Złoto (g)": result_filtered["Gold"].round(2),
    "Srebro (g)": result_filtered["Silver"].round(2),
    "Platyna (g)": result_filtered["Platinum"].round(2),
    "Pallad (g)": result_filtered["Palladium"].round(2),
    "Akcja": result_filtered["Akcja"]
})

# Formatowanie EUR bez miejsc po przecinku
simple_table["Zainwestowane (EUR)"] = simple_table["Zainwestowane (EUR)"].map(lambda x: f"{x:,.0f} EUR")
simple_table["Wartość portfela (EUR)"] = simple_table["Wartość portfela (EUR)"].map(lambda x: f"{x:,.0f} EUR")

# Mniejszy font - używamy st.markdown z HTML
st.markdown(
    simple_table.to_html(index=True, escape=False), 
    unsafe_allow_html=True
)
st.markdown(
    """<style>
    table {
        font-size: 14px; /* mniejszy font w tabeli */
    }
    </style>""",
    unsafe_allow_html=True
)








# 📋 Podsumowanie kosztów magazynowania

# Koszty magazynowania
storage_fees = result[result["Akcja"] == "storage_fee"]

# Całkowity koszt magazynowania
total_storage_cost = storage_fees["Invested"].sum() * (storage_fee / 100) * (1 + vat / 100)

# Okres inwestycyjny w latach
start_date = result.index.min()
end_date = result.index.max()
years = (end_date - start_date).days / 365.25

# Średnioroczny koszt magazynowania
if years > 0:
    avg_annual_storage_cost = total_storage_cost / years
else:
    avg_annual_storage_cost = 0.0

# Koszt magazynowania z ostatniego roku
last_storage_date = storage_fees.index.max()
if pd.notna(last_storage_date):
    last_storage_cost = result.loc[last_storage_date]["Invested"] * (storage_fee / 100) * (1 + vat / 100)
else:
    last_storage_cost = 0.0

# Aktualna wartość portfela
current_portfolio_value = result["Portfolio Value"].iloc[-1]

# Aktualny procentowy koszt magazynowania (za ostatni rok)
if current_portfolio_value > 0:
    storage_cost_percentage = (last_storage_cost / current_portfolio_value) * 100
else:
    storage_cost_percentage = 0.0

st.subheader("📦 Podsumowanie kosztów magazynowania")

col1, col2 = st.columns(2)
with col1:
    st.metric("Średnioroczny koszt magazynowy", f"{avg_annual_storage_cost:,.2f} EUR")
with col2:
    st.metric("Koszt magazynowania (% ostatni rok)", f"{storage_cost_percentage:.2f}%")
