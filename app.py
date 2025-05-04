import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pandas.tseries.offsets import BDay

# =========================================
# 0. Konfiguracja strony i wybór języka
# =========================================

st.set_page_config(page_title="Symulator Metali Szlachetnych", layout="wide")

# 🌐 Ustawienie języka w session_state (trwałe!)
if "language" not in st.session_state:
    st.session_state.language = "Polski"  # domyślny język przy starcie

# Zapisz stan aplikacji w sesji aby można było przełączać widoki
if "show_correlation_analysis" not in st.session_state:
    st.session_state.show_correlation_analysis = False
if "show_trend_comparison" not in st.session_state:
    st.session_state.show_trend_comparison = False
if "last_simulation_result" not in st.session_state:
    st.session_state.last_simulation_result = None
if "last_fixed_result" not in st.session_state:
    st.session_state.last_fixed_result = None

st.sidebar.header("🌐 Wybierz język / Sprache wählen")
language_choice = st.sidebar.selectbox(
    "",
    ("🇵🇱 Polski", "🇩🇪 Deutsch"),
    index=0 if st.session_state.language == "Polski" else 1,
    key="language_selector"
)

# Aktualizacja session_state, jeśli użytkownik zmieni wybór
new_language = "Polski" if "Polski" in language_choice else "Deutsch"
if new_language != st.session_state.language:
    st.session_state.language = new_language
    st.experimental_rerun()  # Przeładowanie strony po zmianie języka

language = st.session_state.language

# =========================================
# 1. Wczytanie danych
# =========================================

@st.cache_data
def load_data():
    """
    Wczytuje dane o cenach metali szlachetnych z pliku CSV.
    """
    try:
        df = pd.read_csv("lbma_data.csv", parse_dates=True, index_col=0)
        df = df.sort_index()
        df = df.dropna()
        
        # Sprawdź integralność danych
        required_columns = ["Gold_EUR", "Silver_EUR", "Platinum_EUR", "Palladium_EUR"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Brakujące kolumny w danych: {', '.join(missing_columns)}")
            return None
            
        return df
    except Exception as e:
        st.error(f"Błąd wczytywania danych: {str(e)}")
        return None

data = load_data()

if data is None:
    st.error("Nie można kontynuować bez odpowiednich danych. Sprawdź plik lbma_data.csv.")
    st.stop()

# =========================================
# 1.1 Wczytanie danych o inflacji
# =========================================

@st.cache_data
def load_inflation_data():
    """
    Wczytuje dane o inflacji z pliku CSV.
    """
    try:
        df = pd.read_csv(
            "inflacja.csv", 
            sep=";", 
            encoding="cp1250"
        )
        df = df[["Rok", "Wartość"]].copy()
        df["Wartość"] = df["Wartość"].str.replace(",", ".").astype(float)
        df["Inflacja (%)"] = df["Wartość"] - 100
        return df[["Rok", "Inflacja (%)"]]
    except Exception as e:
        st.warning(f"Nie można wczytać danych o inflacji: {str(e)}. Używam inflacji zerowej.")
        # Stwórz pusty dataframe z latami z danych i zerową inflacją
        years = range(data.index.min().year, data.index.max().year + 1)
        return pd.DataFrame({"Rok": years, "Inflacja (%)": [0.0] * len(years)})

inflation_real = load_inflation_data()

# =========================================
# 2. Słownik tłumaczeń
# =========================================

translations = {
    "Polski": {
        "portfolio_value": "Wartość portfela",
        "real_portfolio_value": "Wartość portfela (realna, po inflacji)",
        "invested": "Zainwestowane",
        "storage_cost": "Koszty magazynowania",
        "chart_subtitle": "📈 Rozwój wartości portfela: nominalna i realna",
        "summary_title": "📊 Podsumowanie inwestycji",
        "simulation_settings": "⚙️ Parametry Symulacji",
        "investment_amounts": "💰 Inwestycja: Kwoty i daty",
        "metal_allocation": "⚖️ Alokacja metali szlachetnych (%)",
        "recurring_purchases": "🔁 Zakupy cykliczne",
        "rebalancing": "♻️ ReBalancing",
        "storage_costs": "📦 Koszty magazynowania",
        "margins_fees": "📊 Marże i prowizje",
        "buyback_prices": "💵 Ceny odkupu metali",
        "rebalance_prices": "♻️ Ceny ReBalancingu metali",
        "initial_allocation": "Kwota początkowej alokacji (EUR)",
        "first_purchase_date": "Data pierwszego zakupu",
        "last_purchase_date": "Data ostatniego zakupu",
        "purchase_frequency": "Periodyczność zakupów",
        "none": "Brak",
        "week": "Tydzień",
        "month": "Miesiąc",
        "quarter": "Kwartał",
        "purchase_day_of_week": "Dzień tygodnia zakupu",
        "purchase_day_of_month": "Dzień miesiąca zakupu (1–28)",
        "purchase_day_of_quarter": "Dzień kwartału zakupu (1–28)",
        "purchase_amount": "Kwota dokupu (EUR)",
        "rebalance_1": "ReBalancing 1",
        "rebalance_2": "ReBalancing 2",
        "deviation_condition": "Warunek odchylenia wartości",
        "deviation_threshold": "Próg odchylenia (%)",
        "start_rebalance": "Start ReBalancing",
        "monday": "Poniedziałek",
        "tuesday": "Wtorek",
        "wednesday": "Środa",
        "thursday": "Czwartek",
        "friday": "Piątek",
        "trend_strategy": "Strategia TREND",
        "trend_period": "Okres analizy trendu",
        "max_allocation_change": "Maksymalna zmiana alokacji (%)",
        "trend_visualization": "Wizualizacja strategii TREND",
        "correlation_analysis": "Analiza korelacji metali",
        "trend_comparison": "Porównanie z alokacją stałą",
        "current_trends": "Aktualne trendy metali",
        "week_1": "1 tydzień",
        "month_1": "1 miesiąc",
        "month_3": "3 miesiące",
        "year_1": "1 rok",
        "last_purchase": "Od ostatniego zakupu",
        "simple_strategy": "Prosta (na podstawie zmian cen)",
        "momentum_strategy": "Momentum (z uwzględnieniem przyspieszenia)",
        "macd_strategy": "MACD (z sygnałami technicznymi)",
        "export_results": "Eksportuj wyniki",
        "visualization_type": "Typ wizualizacji",
        "line_chart": "Wykres liniowy",
        "area_chart": "Wykres obszarowy",
        "bar_chart": "Wykres słupkowy",
        "help_section": "ℹ️ Pomoc",
        "help_content": """
        ### Jak korzystać z symulatora:
        1. **Alokacja metali**: Ustaw początkowy podział między złoto, srebro, platynę i pallad (suma musi wynosić 100%)
        2. **Zakres czasowy**: Wybierz daty pierwszego i ostatniego zakupu (minimum 7 lat)
        3. **Zakupy cykliczne**: Skonfiguruj regularność dokupów (brak, tygodniowe, miesięczne, kwartalne)
        4. **ReBalancing**: Włącz automatyczne dostosowywanie portfela do zadanej alokacji (opcjonalnie)
        5. **Strategia TREND**: Włącz dynamiczną alokację bazującą na historycznych trendach cenowych (opcjonalnie)
        6. **Koszty**: Dostosuj koszty magazynowania, marże i prowizje
        7. **Uruchom symulację**: Kliknij przycisk na dole menu bocznego
        """,
        "metals": {
            "Gold": "Złoto (Au)",
            "Silver": "Srebro (Ag)",
            "Platinum": "Platyna (Pt)",
            "Palladium": "Pallad (Pd)"
        }
    },
    "Deutsch": {
        "portfolio_value": "Portfoliowert",
        "real_portfolio_value": "Portfoliowert (real, inflationsbereinigt)",
        "invested": "Investiertes Kapital",
        "storage_cost": "Lagerkosten",
        "chart_subtitle": "📈 Entwicklung des Portfoliowerts: nominal und real",
        "summary_title": "📊 Investitionszusammenfassung",
        "simulation_settings": "⚙️ Simulationseinstellungen",
        "investment_amounts": "💰 Investition: Beträge und Daten",
        "metal_allocation": "⚖️ Aufteilung der Edelmetalle (%)",
        "recurring_purchases": "🔁 Regelmäßige Käufe",
        "rebalancing": "♻️ ReBalancing",
        "storage_costs": "📦 Lagerkosten",
        "margins_fees": "📊 Margen und Gebühren",
        "buyback_prices": "💵 Rückkaufpreise der Metalle",
        "rebalance_prices": "♻️ Preise für ReBalancing der Metalle",
        "initial_allocation": "Anfangsinvestition (EUR)",
        "first_purchase_date": "Kaufstartdatum",
        "last_purchase_date": "Letzter Kauftag",
        "purchase_frequency": "Kaufhäufigkeit",
        "none": "Keine",
        "week": "Woche",
        "month": "Monat",
        "quarter": "Quartal",
        "purchase_day_of_week": "Wochentag für Kauf",
        "purchase_day_of_month": "Kauftag im Monat (1–28)",
        "purchase_day_of_quarter": "Kauftag im Quartal (1–28)",
        "purchase_amount": "Kaufbetrag (EUR)",
        "rebalance_1": "ReBalancing 1",
        "rebalance_2": "ReBalancing 2",
        "deviation_condition": "Abweichungsbedingung",
        "deviation_threshold": "Abweichungsschwelle (%)",
        "start_rebalance": "Start des ReBalancing",
        "monday": "Montag",
        "tuesday": "Dienstag",
        "wednesday": "Mittwoch",
        "thursday": "Donnerstag",
        "friday": "Freitag",
        "trend_strategy": "TREND-Strategie",
        "trend_period": "Trendanalysezeitraum",
        "max_allocation_change": "Maximale Allokationsänderung (%)",
        "trend_visualization": "Visualisierung der TREND-Strategie",
        "correlation_analysis": "Metallkorrelationsanalyse",
        "trend_comparison": "Vergleich mit fester Allokation",
        "current_trends": "Aktuelle Metalltrends",
        "week_1": "1 Woche",
        "month_1": "1 Monat",
        "month_3": "3 Monate",
        "year_1": "1 Jahr",
        "last_purchase": "Seit letztem Kauf",
        "simple_strategy": "Einfach (basierend auf Preisänderungen)",
        "momentum_strategy": "Momentum (mit Beschleunigung)",
        "macd_strategy": "MACD (mit technischen Signalen)",
        "export_results": "Ergebnisse exportieren",
        "visualization_type": "Visualisierungstyp",
        "line_chart": "Liniendiagramm",
        "area_chart": "Flächendiagramm",
        "bar_chart": "Balkendiagramm",
        "help_section": "ℹ️ Hilfe",
        "help_content": """
        ### Anleitung zur Verwendung des Simulators:
        1. **Metallallokation**: Legen Sie die Anfangsverteilung zwischen Gold, Silber, Platin und Palladium fest (Summe muss 100% betragen)
        2. **Zeitraum**: Wählen Sie das Datum des ersten und letzten Kaufs (mindestens 7 Jahre)
        3. **Regelmäßige Käufe**: Konfigurieren Sie die Regelmäßigkeit von Käufen (keine, wöchentlich, monatlich, vierteljährlich)
        4. **ReBalancing**: Aktivieren Sie die automatische Anpassung des Portfolios an die gewünschte Allokation (optional)
        5. **TREND-Strategie**: Aktivieren Sie die dynamische Allokation basierend auf historischen Preistrends (optional)
        6. **Kosten**: Passen Sie Lagerkosten, Margen und Gebühren an
        7. **Simulation starten**: Klicken Sie auf die Schaltfläche am unteren Rand der Seitenleiste
        """,
        "metals": {
            "Gold": "Gold (Au)",
            "Silver": "Silber (Ag)",
            "Platinum": "Platin (Pt)",
            "Palladium": "Palladium (Pd)"
        }
    }
}

# =========================================
# 3. Pomocnicze funkcje UI
# =========================================

def show_tooltip(text, help_text):
    """Wyświetla tekst z podpowiedzią"""
    return f"{text} ℹ️" if help_text else text

# =========================================
# 4. Sidebar: Parametry użytkownika
# =========================================

st.sidebar.header(translations[language]["simulation_settings"])

# Dodajemy sekcję pomocy
with st.sidebar.expander(translations[language]["help_section"]):
    st.markdown(translations[language]["help_content"])

# Inwestycja: Kwoty i daty
st.sidebar.subheader(translations[language]["investment_amounts"])

today = datetime.today()
default_initial_date = today.replace(year=today.year - 20)

initial_allocation = st.sidebar.number_input(
    translations[language]["initial_allocation"], 
    value=100000.0, 
    step=100.0,
    help="Kwota początkowej inwestycji w metale szlachetne"
)

initial_date = st.sidebar.date_input(
    translations[language]["first_purchase_date"], 
    value=default_initial_date.date(), 
    min_value=data.index.min().date(), 
    max_value=data.index.max().date(),
    help="Data pierwszego zakupu metali szlachetnych"
)

# Wyznacz minimalną datę końca (initial_date + 7 lat)
min_end_date = (pd.to_datetime(initial_date) + pd.DateOffset(years=7)).date()

if min_end_date > data.index.max().date():
    min_end_date = data.index.max().date()

end_purchase_date = st.sidebar.date_input(
    translations[language]["last_purchase_date"],
    value=data.index.max().date(), 
    min_value=min_end_date, 
    max_value=data.index.max().date(),
    help="Data ostatniego możliwego zakupu (koniec symulacji)"
)

# Obliczenie liczby lat zakupów
days_difference = (pd.to_datetime(end_purchase_date) - pd.to_datetime(initial_date)).days
years_difference = days_difference / 365.25  # uwzględnia przestępne lata

# ✅ / ⚠️ Dynamiczny komunikat
if years_difference >= 7:
    st.sidebar.success(f"✅ Zakres zakupów: {years_difference:.1f} lat.")
    dates_valid = True
else:
    st.sidebar.error(f"⚠️ Zakres zakupów: tylko {years_difference:.1f} lat. (minimum 7 lat wymagane!)")
    dates_valid = False

# Alokacja metali
st.sidebar.subheader(translations[language]["metal_allocation"])

for metal, default in {"Gold": 40, "Silver": 20, "Platinum": 20, "Palladium": 20}.items():
    if f"alloc_{metal}" not in st.session_state:
        st.session_state[f"alloc_{metal}"] = default

if st.sidebar.button("🔄 Resetuj do 40/20/20/20"):
    st.session_state["alloc_Gold"] = 40
    st.session_state["alloc_Silver"] = 20
    st.session_state["alloc_Platinum"] = 20
    st.session_state["alloc_Palladium"] = 20
    st.rerun()

allocation_gold = st.sidebar.slider(translations[language]["metals"]["Gold"], 0, 100, key="alloc_Gold")
allocation_silver = st.sidebar.slider(translations[language]["metals"]["Silver"], 0, 100, key="alloc_Silver")
allocation_platinum = st.sidebar.slider(translations[language]["metals"]["Platinum"], 0, 100, key="alloc_Platinum")
allocation_palladium = st.sidebar.slider(translations[language]["metals"]["Palladium"], 0, 100, key="alloc_Palladium")

total = allocation_gold + allocation_silver + allocation_platinum + allocation_palladium
if total != 100:
    st.title("Symulator ReBalancingu Portfela Metali Szlachetnych")
    st.error(f"❗ Suma alokacji: {total}% – musi wynosić dokładnie 100%, aby kontynuować.")
    st.stop()

allocation = {
    "Gold": allocation_gold / 100,
    "Silver": allocation_silver / 100,
    "Platinum": allocation_platinum / 100,
    "Palladium": allocation_palladium / 100
}

# Zakupy cykliczne
st.sidebar.subheader(translations[language]["recurring_purchases"])

freq_options = {"Brak": "Brak", "Tydzień": "Tydzień", "Miesiąc": "Miesiąc", "Kwartał": "Kwartał"}
if language == "Deutsch":
    freq_options = {"Brak": "Keine", "Tydzień": "Woche", "Miesiąc": "Monat", "Kwartał": "Quartal"}
    
purchase_freq = st.sidebar.selectbox(
    translations[language]["purchase_frequency"], 
    list(freq_options.keys()), 
    index=1,
    format_func=lambda x: freq_options[x],
    help="Jak często dokonywać dokupów metali"
)

if purchase_freq == "Tydzień":
    days_of_week = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]
    if language == "Deutsch":
        days_of_week = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
    
    selected_day = st.sidebar.selectbox(
        translations[language]["purchase_day_of_week"], 
        days_of_week, 
        index=0,
        help="Dzień tygodnia, w którym będą dokonywane zakupy"
    )
    purchase_day = days_of_week.index(selected_day)
    default_purchase_amount = 250.0
elif purchase_freq == "Miesiąc":
    purchase_day = st.sidebar.number_input(
        translations[language]["purchase_day_of_month"], 
        min_value=1, 
        max_value=28, 
        value=1,
        help="Dzień miesiąca (1-28), w którym będą dokonywane zakupy"
    )
    default_purchase_amount = 1000.0
elif purchase_freq == "Kwartał":
    purchase_day = st.sidebar.number_input(
        translations[language]["purchase_day_of_quarter"], 
        min_value=1, 
        max_value=28, 
        value=1,
        help="Dzień kwartału (1-28 pierwszego miesiąca), w którym będą dokonywane zakupy"
    )
    default_purchase_amount = 3250.0
else:
    purchase_day = None
    default_purchase_amount = 0.0

purchase_amount = st.sidebar.number_input(
    translations[language]["purchase_amount"], 
    value=default_purchase_amount, 
    step=50.0,
    help="Kwota przeznaczana na każdy regularny zakup"
)

# ReBalancing
st.sidebar.subheader(translations[language]["rebalancing"])

# Domyślne daty ReBalancingu bazujące na dacie pierwszego zakupu
rebalance_base_year = initial_date.year + 1

rebalance_1_default = datetime(rebalance_base_year, 4, 1)
rebalance_2_default = datetime(rebalance_base_year, 10, 1)

# ReBalancing 1
rebalance_1 = st.sidebar.checkbox(
    translations[language]["rebalance_1"], 
    value=True,
    help="Włącz pierwszy cykliczny rebalancing portfela"
)
rebalance_1_condition = st.sidebar.checkbox(
    translations[language]["deviation_condition"] + " 1", 
    value=False,
    help="Rebalancing 1 nastąpi tylko gdy odchylenie przekroczy próg"
)
rebalance_1_threshold = st.sidebar.number_input(
    translations[language]["deviation_threshold"] + " 1", 
    min_value=0.0, 
    max_value=100.0, 
    value=12.0, 
    step=0.5,
    help="Rebalancing 1 nastąpi tylko gdy odchylenie przekroczy ten próg (w %)"
)

rebalance_1_start = st.sidebar.date_input(
    translations[language]["start_rebalance"] + " 1",
    value=rebalance_1_default.date(),
    min_value=data.index.min().date(),
    max_value=data.index.max().date(),
    help="Data rozpoczęcia pierwszego rebalancingu"
)

# ReBalancing 2
rebalance_2 = st.sidebar.checkbox(
    translations[language]["rebalance_2"], 
    value=False,
    help="Włącz drugi cykliczny rebalancing portfela"
)
rebalance_2_condition = st.sidebar.checkbox(
    translations[language]["deviation_condition"] + " 2", 
    value=False,
    help="Rebalancing 2 nastąpi tylko gdy odchylenie przekroczy próg"
)
rebalance_2_threshold = st.sidebar.number_input(
    translations[language]["deviation_threshold"] + " 2", 
    min_value=0.0, 
    max_value=100.0, 
    value=12.0, 
    step=0.5,
    help="Rebalancing 2 nastąpi tylko gdy odchylenie przekroczy ten próg (w %)"
)

rebalance_2_start = st.sidebar.date_input(
    translations[language]["start_rebalance"] + " 2",
    value=rebalance_2_default.date(),
    min_value=data.index.min().date(),
    max_value=data.index.max().date(),
    help="Data rozpoczęcia drugiego rebalancingu"
)

# ♟️ TREND: Dynamiczna alokacja na podstawie zmian cen

st.sidebar.markdown("---")
st.sidebar.header("♟️ TREND: " + translations[language]["trend_strategy"])

# TREND - aktywacja
trend_active = st.sidebar.checkbox(
    "Aktywuj strategię TREND", 
    value=False,
    help="Włącz dynamiczną alokację na podstawie historycznych zmian cen"
)

# TREND - nowe opcje
if trend_active:
    # Wybór okresu analizy trendu
    trend_period_options = {
        "Od ostatniego zakupu": "last_purchase", 
        "1 tydzień": 7,
        "1 miesiąc": 30, 
        "3 miesiące": 90, 
        "1 rok": 365
    }
    
    # Zmiana nazw dla języka niemieckiego
    if language == "Deutsch":
        trend_period_options = {
            "Seit letztem Kauf": "last_purchase", 
            "1 Woche": 7,
            "1 Monat": 30, 
            "3 Monate": 90, 
            "1 Jahr": 365
        }
    
    trend_period_choice = st.sidebar.selectbox(
        translations[language]["trend_period"],
        options=list(trend_period_options.keys()),
        index=0,
        help="Okres, za który analizowane są zmiany cen metali"
    )
    trend_period = trend_period_options[trend_period_choice]
    
    # Wybór strategii TREND
    trend_strategy_options = {
        "Prosta (na podstawie zmian cen)": "simple", 
        "Momentum (z uwzględnieniem przyspieszenia)": "momentum",
        "MACD (z sygnałami technicznymi)": "macd"
    }
    
    # Zmiana nazw dla języka niemieckiego
    if language == "Deutsch":
        trend_strategy_options = {
            "Einfach (basierend auf Preisänderungen)": "simple", 
            "Momentum (mit Beschleunigung)": "momentum",
            "MACD (mit technischen Signalen)": "macd"
        }
    
    trend_strategy = st.sidebar.selectbox(
        translations[language]["trend_strategy"],
        options=list(trend_strategy_options.keys()),
        index=0,
        help="Metoda analizy trendów i przydzielania alokacji"
    )
    trend_strategy_type = trend_strategy_options[trend_strategy]
    
    # Ograniczenie maksymalnych zmian alokacji
    max_allocation_change = st.sidebar.slider(
        translations[language]["max_allocation_change"],
        min_value=0,
        max_value=100,
        value=50,
        step=5,
        help="Ograniczenie maksymalnej zmiany alokacji pomiędzy zakupami"
    )

# TREND - suwaki przydziału % dla miejsc 1-4
with st.sidebar.expander("⚙️ Ustawienia TREND", expanded=trend_active):
    if "trend_1" not in st.session_state:
        st.session_state["trend_1"] = 40
        st.session_state["trend_2"] = 30
        st.session_state["trend_3"] = 20
        st.session_state["trend_4"] = 10

    if st.button("🔄 Resetuj TREND do 40/30/20/10"):
        st.session_state["trend_1"] = 40
        st.session_state["trend_2"] = 30
        st.session_state["trend_3"] = 20
        st.session_state["trend_4"] = 10
        st.rerun()

    trend_1 = st.slider("📈 Priorytet 1 (najlepszy metal) [%]", 0, 100, key="trend_1", help="Alokacja dla najlepszego metalu")
    trend_2 = st.slider("📈 Priorytet 2 [%]", 0, 100, key="trend_2", help="Alokacja dla drugiego najlepszego metalu")
    trend_3 = st.slider("📉 Priorytet 3 [%]", 0, 100, key="trend_3", help="Alokacja dla trzeciego najlepszego metalu")
    trend_4 = st.slider("📉 Priorytet 4 (najsłabszy metal) [%]", 0, 100, key="trend_4", help="Alokacja dla najsłabszego metalu")

    total_trend = trend_1 + trend_2 + trend_3 + trend_4
    if total_trend != 100:
        st.error(f"❗ Suma przydziału TREND wynosi {total_trend}%. Musi być dokładnie 100%, aby kontynuować.")
        st.stop()

# 📦 Koszty magazynowania
with st.sidebar.expander("📦 " + translations[language]["storage_costs"], expanded=False):
    storage_fee = st.number_input(
        "Roczny koszt magazynowania (%)", 
        value=1.5,
        help="Roczna opłata za przechowywanie metali"
    )
    vat = st.number_input(
        "VAT (%)", 
        value=19.0,
        help="Podatek VAT naliczany na koszty magazynowania"
    )
    storage_metal = st.selectbox(
        "Metal do pokrycia kosztów",
        ["Gold", "Silver", "Platinum", "Palladium", "Best of year", "ALL"],
        help="Metal, który będzie sprzedawany na pokrycie kosztów magazynowania"
    )

# 📊 Marże i prowizje
with st.sidebar.expander("📊 " + translations[language]["margins_fees"], expanded=False):
    margins = {
        "Gold": st.number_input("Marża Gold (%)", value=15.6, help="Narzut na cenę złota przy zakupie"),
        "Silver": st.number_input("Marża Silver (%)", value=18.36, help="Narzut na cenę srebra przy zakupie"),
        "Platinum": st.number_input("Marża Platinum (%)", value=24.24, help="Narzut na cenę platyny przy zakupie"),
        "Palladium": st.number_input("Marża Palladium (%)", value=22.49, help="Narzut na cenę palladu przy zakupie")
    }

# 💵 Ceny odkupu metali od ceny SPOT (-%)
with st.sidebar.expander("💵 " + translations[language]["buyback_prices"], expanded=False):
    buyback_discounts = {
        "Gold": st.number_input("Złoto odk. od SPOT (%)", value=-1.5, step=0.1, help="Zniżka od ceny SPOT przy sprzedaży złota"),
        "Silver": st.number_input("Srebro odk. od SPOT (%)", value=-3.0, step=0.1, help="Zniżka od ceny SPOT przy sprzedaży srebra"),
        "Platinum": st.number_input("Platyna odk. od SPOT (%)", value=-3.0, step=0.1, help="Zniżka od ceny SPOT przy sprzedaży platyny"),
        "Palladium": st.number_input("Pallad odk. od SPOT (%)", value=-3.0, step=0.1, help="Zniżka od ceny SPOT przy sprzedaży palladu")
    }

# ♻️ Ceny ReBalancing metali (%)
with st.sidebar.expander("♻️ " + translations[language]["rebalance_prices"], expanded=False):
    rebalance_markup = {
        "Gold": st.number_input("Złoto ReBalancing (%)", value=6.5, step=0.1, help="Narzut na cenę złota przy rebalancingu"),
        "Silver": st.number_input("Srebro ReBalancing (%)", value=6.5, step=0.1, help="Narzut na cenę srebra przy rebalancingu"),
        "Platinum": st.number_input("Platyna ReBalancing (%)", value=6.5, step=0.1, help="Narzut na cenę platyny przy rebalancingu"),
        "Palladium": st.number_input("Pallad ReBalancing (%)", value=6.5, step=0.1, help="Narzut na cenę palladu przy rebalancingu")
    }

# Opcje wizualizacji
with st.sidebar.expander("📊 Opcje wizualizacji", expanded=False):
    viz_options = ["Wykres liniowy", "Wykres obszarowy", "Wykres słupkowy"]
    if language == "Deutsch":
        viz_options = ["Liniendiagramm", "Flächendiagramm", "Balkendiagramm"]
    
    visualization_type = st.selectbox(
        translations[language]["visualization_type"],
        viz_options,
        index=0,
        help="Typ wykresu do prezentacji wyników"
    )
    
    show_correlation = st.checkbox(
        translations[language]["correlation_analysis"], 
        value=st.session_state.show_correlation_analysis,
        help="Pokaż analizę korelacji między metalami"
    )
    # Aktualizacja stanu
    st.session_state.show_correlation_analysis = show_correlation
    
    if trend_active:
        show_trend_comparison = st.checkbox(
            translations[language]["trend_comparison"], 
            value=st.session_state.show_trend_comparison,
            help="Porównaj strategię TREND ze stałą alokacją"
        )
        # Aktualizacja stanu
        st.session_state.show_trend_comparison = show_trend_comparison

# =========================================
# 5. Funkcje pomocnicze (rozbudowane)
# =========================================

def generate_purchase_dates(start_date, freq, day, end_date):
    """
    Generuje daty zakupów w oparciu o wybraną częstotliwość.
    
    Parameters:
    -----------
    start_date : datetime
        Data początkowa
    freq : str
        Częstotliwość zakupów ("Tydzień", "Miesiąc", "Kwartał" lub "Brak")
    day : int
        Dzień tygodnia/miesiąca/kwartału na zakup
    end_date : datetime
        Data końcowa
        
    Returns:
    --------
    list
        Lista dat zakupów
    """
    dates = []
    current = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)  # upewniamy się, że end_date jest typu datetime

    if freq == "Tydzień":
        while current <= end_date:
            while current.weekday() != day:
                current += timedelta(days=1)
                if current > end_date:
                    break
            if current <= end_date:
                dates.append(current)
            current += timedelta(weeks=1)

    elif freq == "Miesiąc":
        while current <= end_date:
            current = current.replace(day=min(day, 28))
            if current <= end_date:
                dates.append(current)
            current += pd.DateOffset(months=1)

    elif freq == "Kwartał":
        while current <= end_date:
            current = current.replace(day=min(day, 28))
            if current <= end_date:
                dates.append(current)
            current += pd.DateOffset(months=3)

    # Brak zakupów jeśli "Brak"
    return [data.index[data.index.get_indexer([d], method="nearest")][0] for d in dates if len(data.index.get_indexer([d], method="nearest")) > 0]

def find_best_metal_of_year(start_date, end_date):
    """
    Znajduje metal o najlepszych wynikach w danym okresie.
    
    Parameters:
    -----------
    start_date : datetime
        Data początkowa
    end_date : datetime
        Data końcowa
        
    Returns:
    --------
    str
        Nazwa metalu o najlepszych wynikach
    """
    start_prices = data.loc[start_date]
    end_prices = data.loc[end_date]
    growth = {}
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
        growth[metal] = (end_prices[metal + "_EUR"] / start_prices[metal + "_EUR"]) - 1
    return max(growth, key=growth.get)

def calculate_metal_changes(start_date, end_date):
    """
    Oblicza zmiany cen metali między dwiema datami.
    
    Parameters:
    -----------
    start_date : datetime
        Data początkowa
    end_date : datetime
        Data końcowa
        
    Returns:
    --------
    dict
        Słownik z procentowymi zmianami dla każdego metalu
    """
    changes = {}
    prices_start = data.loc[start_date]
    prices_end = data.loc[end_date]
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
        start_price = prices_start[metal + "_EUR"]
        end_price = prices_end[metal + "_EUR"]
        change = (end_price / start_price) - 1
        changes[metal] = change
    return changes

def calculate_momentum_allocation(current_date, period_days, trend_priorities):
    """
    Oblicza alokację na podstawie strategii momentum.
    
    Parameters:
    -----------
    current_date : datetime
        Aktualna data
    period_days : int
        Okres analizy w dniach
    trend_priorities : dict
        Priorytety alokacji dla poszczególnych miejsc (1-4)
        
    Returns:
    --------
    dict
        Słownik z alokacją dla każdego metalu
    """
    # Obliczenie dat dla różnych okresów
    long_period = period_days
    short_period = max(int(period_days / 3), 7)  # krótkookresowo
    
    # Daty
    current_idx = data.index.get_loc(current_date)
    
    # Zapobiegaj wyjściu poza indeks
    if current_idx < long_period:
        long_period = current_idx
    if current_idx < short_period:
        short_period = current_idx
    
    long_start_date = data.index[current_idx - long_period]
    short_start_date = data.index[current_idx - short_period]
    
    # Zmiany cen dla długiego i krótkiego okresu
    long_changes = calculate_metal_changes(long_start_date, current_date)
    short_changes = calculate_metal_changes(short_start_date, current_date)
    
    # Obliczenie "przyspieszenia" jako różnicy między krótkim a długim okresem
    acceleration = {}
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
        acceleration[metal] = short_changes[metal] - (long_changes[metal] * short_period / long_period)
    
    # Normalizacja zmian i przyspieszenia do przedziału [0, 1]
    norm_changes = {}
    if max(long_changes.values()) != min(long_changes.values()):
        for metal, change in long_changes.items():
            norm_changes[metal] = (change - min(long_changes.values())) / (max(long_changes.values()) - min(long_changes.values()))
    else:
        for metal in long_changes:
            norm_changes[metal] = 0.5  # Wszystkie wartości są równe
    
    norm_acceleration = {}
    if max(acceleration.values()) != min(acceleration.values()):
        for metal, acc in acceleration.items():
            norm_acceleration[metal] = (acc - min(acceleration.values())) / (max(acceleration.values()) - min(acceleration.values()))
    else:
        for metal in acceleration:
            norm_acceleration[metal] = 0.5  # Wszystkie wartości są równe
    
    # Połączenie zmian i przyspieszenia z wagami
    momentum_score = {}
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
        momentum_score[metal] = 0.7 * norm_changes[metal] + 0.3 * norm_acceleration[metal]
    
    # Sortowanie metali według wyników momentum
    sorted_metals = sorted(momentum_score.items(), key=lambda x: x[1], reverse=True)
    
    # Przypisanie alokacji według priorytetów
    trend_alloc = {
        sorted_metals[0][0]: trend_priorities[0],
        sorted_metals[1][0]: trend_priorities[1],
        sorted_metals[2][0]: trend_priorities[2],
        sorted_metals[3][0]: trend_priorities[3],
    }
    
    return trend_alloc, sorted_metals

def calculate_macd_allocation(current_date, trend_priorities):
    """
    Oblicza alokację na podstawie sygnałów MACD.
    
    Parameters:
    -----------
    current_date : datetime
        Aktualna data
    trend_priorities : dict
        Priorytety alokacji dla poszczególnych miejsc (1-4)
        
    Returns:
    --------
    dict
        Słownik z alokacją dla każdego metalu
    """
    # Parametry MACD
    fast_window = 12
    slow_window = 26
    signal_window = 9
    
    macd_scores = {}
    
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
        # Pobierz dane historyczne dla metalu
        current_idx = data.index.get_loc(current_date)
        start_idx = max(0, current_idx - slow_window * 2)  # Potrzebujemy więcej danych do poprawnego obliczenia
        
        price_series = data.iloc[start_idx:current_idx+1][metal + "_EUR"]
        
        # Oblicz EMA (wykładnicze średnie kroczące)
        ema_fast = price_series.ewm(span=fast_window, adjust=False).mean()
        ema_slow = price_series.ewm(span=slow_window, adjust=False).mean()
        
        # Oblicz MACD i linię sygnału
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_window, adjust=False).mean()
        
        # Oblicz histogram MACD
        histogram = macd_line - signal_line
        
        # Wyznacz siłę trendu na podstawie histogramu i kierunku MACD
        current_macd = macd_line.iloc[-1]
        prev_macd = macd_line.iloc[-2] if len(macd_line) > 1 else 0
        
        current_histogram = histogram.iloc[-1]
        prev_histogram = histogram.iloc[-2] if len(histogram) > 1 else 0
        
        # Punktacja:
        # - Jeśli MACD > 0 i rośnie: 👍
        # - Jeśli MACD > 0 ale spada: 👍 ale mniej
        # - Jeśli MACD < 0 ale rośnie: 👎 ale mniej
        # - Jeśli MACD < 0 i spada: 👎
        
        # Bazowa punktacja
        base_score = 1.0 if current_macd > 0 else 0.0
        
        # Modyfikator kierunku
        direction_mod = 0.5 if current_macd > prev_macd else -0.5
        
        # Modyfikator histogramu (siła trendu)
        hist_mod = 0.3 if abs(current_histogram) > abs(prev_histogram) else -0.3
        
        # Połączona ocena
        macd_scores[metal] = base_score + direction_mod + hist_mod
    
    # Sortowanie metali według wyników MACD
    sorted_metals = sorted(macd_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Przypisanie alokacji według priorytetów
    trend_alloc = {
        sorted_metals[0][0]: trend_priorities[0],
        sorted_metals[1][0]: trend_priorities[1],
        sorted_metals[2][0]: trend_priorities[2],
        sorted_metals[3][0]: trend_priorities[3],
    }
    
    return trend_alloc, sorted_metals

def calculate_trend_allocation(current_date, last_purchase_date, trend_period, trend_strategy_type, trend_priorities):
    """
    Oblicza alokację dla strategii TREND na podstawie wybranej metody.
    
    Parameters:
    -----------
    current_date : datetime
        Aktualna data
    last_purchase_date : datetime
        Data ostatniego zakupu
    trend_period : str or int
        Okres analizy ('last_purchase' lub liczba dni)
    trend_strategy_type : str
        Typ strategii ('simple', 'momentum', 'macd')
    trend_priorities : list
        Lista wartości priorytetów dla miejsc 1-4
        
    Returns:
    --------
    dict
        Słownik z alokacją dla każdego metalu
    """
    # Ustal datę początkową analizy
    if trend_period == "last_purchase":
        start_date = last_purchase_date
    else:
        # Oblicz datę początkową na podstawie liczby dni
        days = int(trend_period)
        start_date_raw = current_date - pd.Timedelta(days=days)
        # Znajdź najbliższą datę w danych
        start_date = data.index[data.index.get_indexer([start_date_raw], method="nearest")][0]
    
    # Konwersja priorytetów na ułamki (dzielenie przez 100)
    trend_priorities_fraction = [
        trend_priorities[0] / 100,
        trend_priorities[1] / 100,
        trend_priorities[2] / 100,
        trend_priorities[3] / 100
    ]
    
    # Wybór odpowiedniej strategii
    if trend_strategy_type == "simple":
        # Prosta strategia - alokacja na podstawie zmian cen
        changes = calculate_metal_changes(start_date, current_date)
        sorted_metals = sorted(changes.items(), key=lambda x: x[1], reverse=True)
        
        trend_alloc = {
            sorted_metals[0][0]: trend_priorities_fraction[0],
            sorted_metals[1][0]: trend_priorities_fraction[1],
            sorted_metals[2][0]: trend_priorities_fraction[2],
            sorted_metals[3][0]: trend_priorities_fraction[3],
        }
        return trend_alloc, sorted_metals
        
    elif trend_strategy_type == "momentum":
        # Strategia momentum
        if trend_period == "last_purchase":
            period_days = (current_date - last_purchase_date).days
            if period_days < 7:  # Zabezpieczenie przed zbyt krótkim okresem
                period_days = 30
        else:
            period_days = int(trend_period)
        
        return calculate_momentum_allocation(current_date, period_days, trend_priorities_fraction)
        
    elif trend_strategy_type == "macd":
        # Strategia MACD
        return calculate_macd_allocation(current_date, trend_priorities_fraction)
    
    # Domyślnie zwróć prostą strategię
    changes = calculate_metal_changes(start_date, current_date)
    sorted_metals = sorted(changes.items(), key=lambda x: x[1], reverse=True)
    
    trend_alloc = {
        sorted_metals[0][0]: trend_priorities_fraction[0],
        sorted_metals[1][0]: trend_priorities_fraction[1],
        sorted_metals[2][0]: trend_priorities_fraction[2],
        sorted_metals[3][0]: trend_priorities_fraction[3],
    }
    return trend_alloc, sorted_metals

def apply_allocation_limit(new_alloc, prev_alloc, max_change_percent):
    """
    Ogranicza maksymalne zmiany alokacji między zakupami.
    
    Parameters:
    -----------
    new_alloc : dict
        Nowa alokacja
    prev_alloc : dict
        Poprzednia alokacja
    max_change_percent : float
        Maksymalna zmiana w procentach
        
    Returns:
    --------
    dict
        Ograniczona alokacja
    """
    if prev_alloc is None:
        return new_alloc
    
    max_change = max_change_percent / 100
    final_alloc = {}
    
    for metal in new_alloc:
        prev = prev_alloc.get(metal, 0)
        curr = new_alloc[metal]
        
        # Ogranicz zmianę do zadanego procentu
        if curr > prev:
            final_alloc[metal] = min(curr, prev + max_change)
        else:
            final_alloc[metal] = max(curr, prev - max_change)
    
    # Normalizuj alokację, aby suma była 1.0
    total = sum(final_alloc.values())
    normalized_alloc = {m: v/total for m, v in final_alloc.items()}
    
    return normalized_alloc

def simulate(allocation, use_trend=False, fixed_allocation=False):
    """
    Symuluje portfel metali szlachetnych w czasie.
    
    Parameters:
    -----------
    allocation : dict
        Słownik z początkową alokacją dla każdego metalu
    use_trend : bool
        Czy użyć strategii TREND
    fixed_allocation : bool
        Czy używać stałej alokacji nawet gdy TREND jest aktywny
        
    Returns:
    --------
    pd.DataFrame
        DataFrame z wynikami symulacji
    """
    portfolio = {m: 0.0 for m in allocation}
    history = []
    invested = 0.0
    trend_history = []  # Historia działania TREND

    all_dates = data.loc[initial_date:end_purchase_date].index
    purchase_dates = generate_purchase_dates(initial_date, purchase_freq, purchase_day, end_purchase_date)

    last_year = None
    last_purchase_date = pd.to_datetime(initial_date)

    last_rebalance_dates = {
        "rebalance_1": None,
        "rebalance_2": None
    }
    
    # Przechowywanie poprzedniej alokacji TREND
    previous_trend_alloc = None

    def apply_rebalance(d, label, condition_enabled, threshold_percent):
        nonlocal last_rebalance_dates

        min_days_between_rebalances = 30  # minimalny odstęp w dniach

        last_date = last_rebalance_dates.get(label)
        if last_date is not None and (d - last_date).days < min_days_between_rebalances:
            return f"rebalancing_skipped_{label}_too_soon"

        prices = data.loc[d]
        total_value = sum(prices[m + "_EUR"] * portfolio[m] for m in allocation)

        if total_value == 0:
            return f"rebalancing_skipped_{label}_no_value"

        current_shares = {
            m: (prices[m + "_EUR"] * portfolio[m]) / total_value
            for m in allocation
        }

        rebalance_trigger = False
        for metal in allocation:
            deviation = abs(current_shares[metal] - allocation[metal]) * 100
            if deviation >= threshold_percent:
                rebalance_trigger = True
                break

        if condition_enabled and not rebalance_trigger:
            return f"rebalancing_skipped_{label}_no_deviation"

        target_value = {m: total_value * allocation[m] for m in allocation}

        for metal in allocation:
            current_value = prices[metal + "_EUR"] * portfolio[metal]
            diff = current_value - target_value[metal]

            if diff > 0:
                sell_price = prices[metal + "_EUR"] * (1 + buyback_discounts[metal] / 100)
                grams_to_sell = min(diff / sell_price, portfolio[metal])
                portfolio[metal] -= grams_to_sell
                cash = grams_to_sell * sell_price

                for buy_metal in allocation:
                    needed_value = target_value[buy_metal] - prices[buy_metal + "_EUR"] * portfolio[buy_metal]
                    if needed_value > 0:
                        buy_price = prices[buy_metal + "_EUR"] * (1 + rebalance_markup[buy_metal] / 100)
                        buy_grams = min(cash / buy_price, needed_value / buy_price)
                        portfolio[buy_metal] += buy_grams
                        cash -= buy_grams * buy_price
                        if cash <= 0:
                            break

        last_rebalance_dates[label] = d
        return label

    # Początkowy zakup (standardowo, wg allocation)
    initial_ts = data.index[data.index.get_indexer([pd.to_datetime(initial_date)], method="nearest")][0]
    prices = data.loc[initial_ts]
    for metal, percent in allocation.items():
        price = prices[metal + "_EUR"] * (1 + margins[metal] / 100)
        grams = (initial_allocation * percent) / price
        portfolio[metal] += grams
    invested += initial_allocation
    history.append((initial_ts, invested, dict(portfolio), "initial"))

    for d in all_dates:
        actions = []

        if d in purchase_dates:
            prices = data.loc[d]

            if use_trend and not fixed_allocation:
                # Obliczenie alokacji TREND
                trend_alloc, sorted_metals = calculate_trend_allocation(
                    d, 
                    last_purchase_date, 
                    trend_period, 
                    trend_strategy_type, 
                    [trend_1, trend_2, trend_3, trend_4]
                )
                
                # Ograniczenie maksymalnych zmian alokacji
                if previous_trend_alloc and max_allocation_change < 100:
                    trend_alloc = apply_allocation_limit(trend_alloc, previous_trend_alloc, max_allocation_change)
                
                # Zapisz aktualną alokację jako poprzednią dla następnego zakupu
                previous_trend_alloc = dict(trend_alloc)
                
                # Zapisz historię TREND
                trend_history.append({
                    "Date": d,
                    "Start Date": d - pd.Timedelta(days=30) if trend_period == "last_purchase" else d - pd.Timedelta(days=int(trend_period)),
                    "Strategy": trend_strategy_type,
                    "Best Metal": sorted_metals[0][0],
                    "Best Change": sorted_metals[0][1],
                    "Worst Metal": sorted_metals[-1][0],
                    "Worst Change": sorted_metals[-1][1],
                    "Allocations": {m: round(trend_alloc[m] * 100, 1) for m in trend_alloc}
                })
            else:
                # Standardowa alokacja
                trend_alloc = allocation

            for metal, percent in trend_alloc.items():
                price = prices[metal + "_EUR"] * (1 + margins[metal] / 100)
                grams = (purchase_amount * percent) / price
                portfolio[metal] += grams

            invested += purchase_amount
            actions.append("recurring")

            # 🔵 Aktualizacja daty ostatniego zakupu
            last_purchase_date = d

        # ReBalancing 1
        if rebalance_1 and d >= pd.to_datetime(rebalance_1_start) and d.month == rebalance_1_start.month and d.day == rebalance_1_start.day:
            actions.append(apply_rebalance(d, "rebalance_1", rebalance_1_condition, rebalance_1_threshold))

        # ReBalancing 2
        if rebalance_2 and d >= pd.to_datetime(rebalance_2_start) and d.month == rebalance_2_start.month and d.day == rebalance_2_start.day:
            actions.append(apply_rebalance(d, "rebalance_2", rebalance_2_condition, rebalance_2_threshold))

        # Koszty magazynowania co rok
        if last_year is None:
            last_year = d.year

        if d.year != last_year:
            last_year_end = data.loc[data.index[data.index.year == last_year]].index[-1]
            storage_cost = invested * (storage_fee / 100) * (1 + vat / 100)
            prices_end = data.loc[last_year_end]

            if storage_metal == "Best of year":
                metal_to_sell = find_best_metal_of_year(
                    data.index[data.index.year == last_year][0],
                    data.index[data.index.year == last_year][-1]
                )
                sell_price = prices_end[metal_to_sell + "_EUR"] * (1 + buyback_discounts[metal_to_sell] / 100)
                grams_needed = storage_cost / sell_price
                grams_needed = min(grams_needed, portfolio[metal_to_sell])
                portfolio[metal_to_sell] -= grams_needed

            elif storage_metal == "ALL":
                total_value = sum(prices_end[m + "_EUR"] * portfolio[m] for m in allocation)
                for metal in allocation:
                    share = (prices_end[metal + "_EUR"] * portfolio[metal]) / total_value
                    cash_needed = storage_cost * share
                    sell_price = prices_end[metal + "_EUR"] * (1 + buyback_discounts[metal] / 100)
                    grams_needed = cash_needed / sell_price
                    grams_needed = min(grams_needed, portfolio[metal])
                    portfolio[metal] -= grams_needed

            else:
                sell_price = prices_end[storage_metal + "_EUR"] * (1 + buyback_discounts[storage_metal] / 100)
                grams_needed = storage_cost / sell_price
                grams_needed = min(grams_needed, portfolio[storage_metal])
                portfolio[storage_metal] -= grams_needed

            history.append((last_year_end, invested, dict(portfolio), "storage_fee"))
            last_year = d.year

        if actions:
            history.append((d, invested, dict(portfolio), ", ".join(actions)))

    # Tworzenie dataframe wynikowego
    df_result = pd.DataFrame([{
        "Date": h[0],
        "Invested": h[1],
        **{m: h[2][m] for m in allocation},
        "Portfolio Value": sum(
            data.loc[h[0]][m + "_EUR"] * (1 + buyback_discounts[m] / 100) * h[2][m]
            for m in allocation
        ),
        "Akcja": h[3]
    } for h in history]).set_index("Date")
    
    # Dołącz informacje o historii TREND
    if trend_history:
        df_trend = pd.DataFrame(trend_history)
        return df_result, df_trend
    
    return df_result, None

# =========================================
# 6. Główna sekcja aplikacji
# =========================================

st.title("Symulator ReBalancingu Portfela Metali Szlachetnych")
st.markdown("---")

# Uruchom symulację po kliknięciu przycisku
if dates_valid:
    start_simulation = st.sidebar.button("🚀 Uruchom symulację")
else:
    st.sidebar.button("🚀 Uruchom symulację", disabled=True)
    start_simulation = False

# Jeśli przycisk został kliknięty lub istnieją już wyniki w pamięci, pokaż wyniki
if start_simulation or st.session_state.last_simulation_result is not None:
    with st.spinner("Trwa symulacja..."):
        if start_simulation:
            # Uruchom nową symulację
            result, trend_data = simulate(allocation, use_trend=trend_active)
            st.session_state.last_simulation_result = result
            st.session_state.last_trend_data = trend_data
            
            # Jeśli porównanie TREND jest włączone, uruchom symulację ze stałą alokacją
            if trend_active and st.session_state.show_trend_comparison:
                result_fixed, _ = simulate(allocation, use_trend=False)
                st.session_state.last_fixed_result = result_fixed
        else:
            # Użyj zapisanych wyników
            result = st.session_state.last_simulation_result
            trend_data = st.session_state.last_trend_data if 'last_trend_data' in st.session_state else None
    
    # === Korekta wartości portfela o realną inflację ===
    
    # Słownik: Rok -> Inflacja
    inflation_dict = dict(zip(inflation_real["Rok"], inflation_real["Inflacja (%)"]))
    
    # Funkcja: obliczenie skumulowanej inflacji od startu
    def calculate_cumulative_inflation(start_year, current_year):
        """Oblicza skumulowany współczynnik inflacji między dwoma latami"""
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
    
    # 📈 Wykres wartości portfela: nominalna vs realna vs inwestycje vs koszty magazynowania
    
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
    
    # Nagłówki bardziej czytelne
    chart_data.rename(columns={
        "Portfolio Value": f"💰 {translations[language]['portfolio_value']}",
        "Portfolio Value Real": f"🏛️ {translations[language]['real_portfolio_value']}",
        "Invested": f"💵 {translations[language]['invested']}",
        "Storage Cost": f"📦 {translations[language]['storage_cost']}"
    }, inplace=True)
    
    # 📈 Ładny interaktywny wykres w Streamlit
    st.subheader(translations[language]["chart_subtitle"])
    
    # Wybór typu wykresu
    if visualization_type == "Wykres liniowy" or visualization_type == "Liniendiagramm":
        st.line_chart(chart_data)
    elif visualization_type == "Wykres obszarowy" or visualization_type == "Flächendiagramm":
        st.area_chart(chart_data)
    else:  # Wykres słupkowy
        st.bar_chart(chart_data)
    
    # Eksport wyników do CSV
    csv_data = result.to_csv().encode('utf-8')
    st.download_button(
        label="📥 " + translations[language]["export_results"],
        data=csv_data,
        file_name="portfolio_simulation.csv",
        mime="text/csv",
        help="Pobierz wyniki symulacji jako plik CSV"
    )
    
    # Podsumowanie wyników
    st.subheader(translations[language]["summary_title"])
    
    start_date = result.index.min()
    end_date = result.index.max()
    years = (end_date - start_date).days / 365.25
    
    alokacja_kapitalu = result["Invested"].max()
    wartosc_metali = result["Portfolio Value"].iloc[-1]
    wartosc_realna = result["Portfolio Value Real"].iloc[-1]
    
    if alokacja_kapitalu > 0 and years > 0:
        roczny_procent = (wartosc_metali / alokacja_kapitalu) ** (1 / years) - 1
        roczny_procent_realny = (wartosc_realna / alokacja_kapitalu) ** (1 / years) - 1
    else:
        roczny_procent = 0.0
        roczny_procent_realny = 0.0

    # Wyświetlenie wyników w formie kart
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💶 Zainwestowany kapitał", f"{alokacja_kapitalu:,.2f} EUR")
        st.metric("📈 Roczny zwrot (nominalny)", f"{roczny_procent * 100:.2f}%")
    with col2:
        st.metric("📦 Wartość końcowa portfela", f"{wartosc_metali:,.2f} EUR")
        st.metric("📉 Roczny zwrot (realny, po inflacji)", f"{roczny_procent_realny * 100:.2f}%")
    
    # Wykres składu portfela (kołowy)
    st.subheader("⚖️ Skład końcowy portfela")
    
    final_composition = {}
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
        final_composition[metal] = result.iloc[-1][metal] * data.loc[result.index[-1]][metal + "_EUR"] * (1 + buyback_discounts[metal] / 100)
    
    # Kolory metali
    metal_colors = {
        "Gold": "#D4AF37",      # złoto 
        "Silver": "#C0C0C0",    # srebro
        "Platinum": "#E5E4E2",  # platyna
        "Palladium": "#CED0DD"  # pallad
    }
    
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        final_composition.values(), 
        labels=final_composition.keys(),
        autopct='%1.1f%%',
        startangle=90,
        colors=[metal_colors[metal] for metal in final_composition.keys()]
    )
    
    # Równe proporcje, aby koło było okrągłe
    ax.axis('equal')
    plt.title("Skład końcowy portfela według wartości")
    
    st.pyplot(fig)
    
    # Wzrost cen metali od początku inwestycji
    st.subheader("📊 Wzrost cen metali od startu inwestycji")
    
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
        st.metric("Złoto (Au)", f"{wzrosty['Gold']:.2f}%", delta=f"{wzrosty['Gold']:.1f}%")
    with col2:
        st.metric("Srebro (Ag)", f"{wzrosty['Silver']:.2f}%", delta=f"{wzrosty['Silver']:.1f}%")
    with col3:
        st.metric("Platyna (Pt)", f"{wzrosty['Platinum']:.2f}%", delta=f"{wzrosty['Platinum']:.1f}%")
    with col4:
        st.metric("Pallad (Pd)", f"{wzrosty['Palladium']:.2f}%", delta=f"{wzrosty['Palladium']:.1f}%")
    
    # Aktualnie posiadane ilości metali
    st.subheader("⚖️ Aktualnie posiadane ilości metali (g)")
    
    # Aktualne ilości gramów z ostatniego dnia
    aktualne_ilosci = {
        "Gold": result.iloc[-1]["Gold"],
        "Silver": result.iloc[-1]["Silver"],
        "Platinum": result.iloc[-1]["Platinum"],
        "Palladium": result.iloc[-1]["Palladium"]
    }
    
    # Wyświetlenie w czterech kolumnach z kolorowym napisem
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"<h4 style='color:{metal_colors['Gold']}; text-align: center;'>Złoto (Au)</h4>", unsafe_allow_html=True)
        st.metric(label="", value=f"{aktualne_ilosci['Gold']:.2f} g")
    with col2:
        st.markdown(f"<h4 style='color:{metal_colors['Silver']}; text-align: center;'>Srebro (Ag)</h4>", unsafe_allow_html=True)
        st.metric(label="", value=f"{aktualne_ilosci['Silver']:.2f} g")
    with col3:
        st.markdown(f"<h4 style='color:{metal_colors['Platinum']}; text-align: center;'>Platyna (Pt)</h4>", unsafe_allow_html=True)
        st.metric(label="", value=f"{aktualne_ilosci['Platinum']:.2f} g")
    with col4:
        st.markdown(f"<h4 style='color:{metal_colors['Palladium']}; text-align: center;'>Pallad (Pd)</h4>", unsafe_allow_html=True)
        st.metric(label="", value=f"{aktualne_ilosci['Palladium']:.2f} g")
    
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
    
    # Analiza korelacji metali (jeśli włączona)
    if st.session_state.show_correlation_analysis:
        st.subheader("📉 Analiza korelacji metali")
        
        # Przygotuj dane cen
        price_data = pd.DataFrame({
            "Gold": data["Gold_EUR"],
            "Silver": data["Silver_EUR"],
            "Platinum": data["Platinum_EUR"],
            "Palladium": data["Palladium_EUR"]
        })
        
        # Oblicz macierz korelacji
        corr_matrix = price_data.pct_change().corr()
        
        # Wyświetl macierz korelacji jako ciepłą mapę
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", ax=ax)
        plt.title("Korelacja zmian cen metali szlachetnych")
        st.pyplot(fig)
        
        st.write("""
        Mapa korelacji pokazuje, jak zmiany cen poszczególnych metali są ze sobą powiązane:
        - Wartości bliskie 1 oznaczają silną dodatnią korelację (metale poruszają się razem)
        - Wartości bliskie -1 oznaczają silną ujemną korelację (metale poruszają się przeciwnie)
        - Wartości bliskie 0 oznaczają brak korelacji
        
        Strategia TREND może być skuteczniejsza przy niższej korelacji między metalami.
        """)
    
    # Analiza strategii TREND (jeśli aktywna)
    if trend_active and trend_data is not None:
        st.subheader("♟️ Analiza strategii TREND")
        
        # Wyświetl informacje o działaniu strategii TREND
        st.write("Strategia TREND dynamicznie zmienia alokację metali na podstawie historycznych zmian cen.")
        
        # Histogram best/worst metali
        best_metals = pd.Series([record["Best Metal"] for record in trend_data.to_dict('records')]).value_counts()
        worst_metals = pd.Series([record["Worst Metal"] for record in trend_data.to_dict('records')]).value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Najlepsze metale")
            fig, ax = plt.subplots()
            best_metals.plot(kind='bar', ax=ax, color='green')
            plt.title("Liczba wystąpień jako najlepszy metal")
            plt.ylabel("Liczba wystąpień")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.subheader("Najgorsze metale")
            fig, ax = plt.subplots()
            worst_metals.plot(kind='bar', ax=ax, color='red')
            plt.title("Liczba wystąpień jako najgorszy metal")
            plt.ylabel("Liczba wystąpień")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        
        # Wyświetl tabelę z alokacjami TREND
        st.subheader("Historia alokacji TREND")
        
        # Przygotuj dane do wyświetlenia
        trend_display = trend_data[["Date", "Strategy", "Best Metal", "Worst Metal"]].copy()
        
        # Dodaj kolumny z alokacjami
        for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
            trend_display[f"{metal} %"] = trend_display.apply(
                lambda row: row["Allocations"][metal] if isinstance(row["Allocations"], dict) else 0, 
                axis=1
            )
        
        # Wyświetl tabelę
        st.dataframe(trend_display[["Date", "Strategy", "Best Metal", "Worst Metal", "Gold %", "Silver %", "Platinum %", "Palladium %"]])
        
        # Porównanie z alokacją stałą
        if st.session_state.show_trend_comparison and st.session_state.last_fixed_result is not None:
            st.subheader("Porównanie strategii TREND ze stałą alokacją")
            
            # Pobierz wyniki dla stałej alokacji
            result_fixed = st.session_state.last_fixed_result
            
            # Porównaj wyniki
            comparison = pd.DataFrame({
                "Stała alokacja": result_fixed["Portfolio Value"],
                "Strategia TREND": result["Portfolio Value"]
            })
            
            # Oblicz różnicę procentową
            final_fixed = result_fixed["Portfolio Value"].iloc[-1]
            final_trend = result["Portfolio Value"].iloc[-1]
            diff_pct = ((final_trend / final_fixed) - 1) * 100
            
            st.metric(
                "Różnica w końcowej wartości portfela", 
                f"{diff_pct:.2f}%",
                delta=f"{diff_pct:.2f}%"
            )
            
            # Wyświetl wykres porównawczy
            st.line_chart(comparison)
    
    # Wyświetl dashboard aktualnych trendów metali
    st.subheader("📈 Aktualne trendy metali szlachetnych")
    
    # Oblicz zmiany dla różnych okresów
    trend_periods = {
        "1 tydzień": 7,
        "1 miesiąc": 30,
        "3 miesiące": 90,
        "1 rok": 365
    }
    
    if language == "Deutsch":
        trend_periods = {
            "1 Woche": 7,
            "1 Monat": 30,
            "3 Monate": 90,
            "1 Jahr": 365
        }
    
    # Znajdź najnowszą datę w danych
    latest_date = data.index.max()
    
    # Przygotuj dane o trendach
    trend_data_display = []
    
    for period_name, days in trend_periods.items():
        start_date = latest_date - pd.Timedelta(days=days)
        start_date = data.index[data.index.get_indexer([start_date], method="nearest")][0]
        
        changes = {}
        for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
            start_price = data.loc[start_date, metal + "_EUR"]
            end_price = data.loc[latest_date, metal + "_EUR"]
            change = ((end_price / start_price) - 1) * 100
            changes[metal] = change
        
        trend_data_display.append({
            "Period": period_name,
            **changes
        })
    
    # Stwórz DataFrame i wyświetl
    trend_df = pd.DataFrame(trend_data_display)
    trend_df = trend_df.set_index("Period")
    
    # Popraw formatowanie: dodaj znak % i koloruj pozytywne/negatywne wartości
    def color_cells(val):
        color = 'green' if val >= 0 else 'red'
        return f'color: {color}'
    
    # Formatuj DataFrame
    styled_trend_df = trend_df.style.format("{:.2f}%")
    styled_trend_df = styled_trend_df.applymap(color_cells)
    
    st.dataframe(styled_trend_df)
    
    # Wykres trendów metali
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
        ax.plot(trend_df.index, trend_df[metal], label=metal, marker='o', color=metal_colors[metal])
    
    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    ax.set_title('Zmiany cen metali szlachetnych w różnych okresach')
    ax.set_ylabel('Zmiana (%)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)
    
    # Historyczne dane w formie tabeli
    st.subheader("📅 Podgląd danych historycznych (pierwszy dzień każdego roku)")
    
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
    
    # Wyświetl tabelę
    st.dataframe(simple_table)
    
    # Podsumowanie kosztów magazynowania
    st.subheader("📦 Podsumowanie kosztów magazynowania")
    
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
    last_storage_date = storage_fees.index.max() if not storage_fees.empty else None
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
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Średnioroczny koszt magazynowy", f"{avg_annual_storage_cost:,.2f} EUR")
    with col2:
        st.metric("Koszt magazynowania (% ostatni rok)", f"{storage_cost_percentage:.2f}%")
    
    # Całkowity koszt magazynowania i jako procent wartości końcowej
    st.metric("Całkowity koszt magazynowania", f"{total_storage_cost:,.2f} EUR")
    
    if current_portfolio_value > 0:
        total_storage_percentage = (total_storage_cost / current_portfolio_value) * 100
        st.caption(f"Całkowity koszt magazynowania stanowi {total_storage_percentage:.2f}% końcowej wartości portfela")

else:
    # Jeśli nie rozpoczęto symulacji, wyświetl instrukcje
    st.info("👈 Ustaw parametry symulacji w menu bocznym i kliknij 'Uruchom symulację'.")
    
    # Wyświetl przykładowy wykres danych historycznych cen metali
    st.subheader("📈 Historyczne ceny metali szlachetnych (EUR/g)")
    
    # Przygotuj dane do wykresu
    price_chart_data = data[["Gold_EUR", "Silver_EUR", "Platinum_EUR", "Palladium_EUR"]].copy()
    
    # Zmień nazwy kolumn dla czytelności
    price_chart_data.rename(columns={
        "Gold_EUR": "Złoto (Au)",
        "Silver_EUR": "Srebro (Ag)",
        "Platinum_EUR": "Platyna (Pt)",
        "Palladium_EUR": "Pallad (Pd)"
    }, inplace=True)
    
    # Wyświetl wykres
    st.line_chart(price_chart_data)
    
    st.write("""
    ### Witaj w Symulatorze ReBalancingu Portfela Metali Szlachetnych!
    
    Ta aplikacja pozwala symulować różne strategie inwestycyjne dla portfela złota, srebra, platyny i palladu.
    
    Główne funkcje:
    - Ustalanie początkowej alokacji metali
    - Symulacja regularnych zakupów
    - Automatyczny rebalancing portfela
    - Strategia TREND dopasowująca alokację do historycznych zmian cen
    - Uwzględnianie kosztów magazynowania i inflacji
    
    Aby rozpocząć, skonfiguruj parametry w menu bocznym i kliknij "Uruchom symulację".
    """)
