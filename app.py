import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Konfiguracja strony
st.set_page_config(page_title="Symulator Metali Szlachetnych", layout="wide")

# =========================================
# 0. Funkcje wczytania danych
# =========================================

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

# =========================================
# 1. Wybór języka
# =========================================

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

# =========================================
# 2. Tłumaczenia (jeśli masz swój słownik translations)
# =========================================

translations = {
    "Polski": {
        "portfolio_value": "Wartość portfela",
        "real_portfolio_value": "Wartość portfela (realna, po inflacji)",
        "invested": "Zainwestowane",
        "storage_cost": "Koszty magazynowania",
        "chart_subtitle": "📈 Rozwój wartości portfela: nominalna i realna",
        "summary_title": "📊 Podsumowanie inwestycji",
        "simulation_settings": "⚙️ Parametry Symulacji"
    },
    "Deutsch": {
        "portfolio_value": "Portfoliowert",
        "real_portfolio_value": "Portfoliowert (real, inflationsbereinigt)",
        "invested": "Investiertes Kapital",
        "storage_cost": "Lagerkosten",
        "chart_subtitle": "📈 Entwicklung des Portfoliowerts: nominal und real",
        "summary_title": "📊 Investitionszusammenfassung",
        "simulation_settings": "⚙️ Simulationseinstellungen"
    }
}






# =========================================
# 3. Parametry użytkownika w Expanders
# =========================================

st.title("Symulator ReBalancingu Portfela Metali Szlachetnych")
st.markdown("---")

# -- Inwestycja: Kwoty i daty
with st.expander("💰 Inwestycja: Kwoty i daty", expanded=True):
    today = datetime.today()
    default_initial_date = today.replace(year=today.year - 20)

    initial_allocation = st.number_input(
        "Kwota początkowej alokacji (EUR)", 
        value=100000.0, 
        step=100.0
    )

    initial_date = st.date_input(
        "Data pierwszego zakupu",
        value=default_initial_date.date(),
        min_value=data.index.min().date(),
        max_value=data.index.max().date()
    )

    # Wyznaczenie minimalnej daty końcowej
    min_end_date = (pd.to_datetime(initial_date) + pd.DateOffset(years=7)).date()
    if min_end_date > data.index.max().date():
        min_end_date = data.index.max().date()

    end_purchase_date = st.date_input(
        "Data ostatniego zakupu",
        value=data.index.max().date(),
        min_value=min_end_date,
        max_value=data.index.max().date()
    )

    # Walidacja liczby lat
    days_difference = (pd.to_datetime(end_purchase_date) - pd.to_datetime(initial_date)).days
    years_difference = days_difference / 365.25

    if years_difference >= 7:
        st.success(f"✅ Zakres zakupów: {years_difference:.1f} lat.")
        dates_valid = True
    else:
        st.error(f"⚠️ Zakres zakupów: tylko {years_difference:.1f} lat. (minimum 7 lat wymagane!)")
        dates_valid = False

# -- Alokacja metali
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

# Alokacja zapisuje się jako słownik
allocation = {
    "Gold": allocation_gold / 100,
    "Silver": allocation_silver / 100,
    "Platinum": allocation_platinum / 100,
    "Palladium": allocation_palladium / 100
}

# -- Zakupy cykliczne
with st.expander("🔁 Zakupy cykliczne", expanded=True):
    purchase_freq = st.selectbox("Periodyczność zakupów", ["Brak", "Tydzień", "Miesiąc", "Kwartał"], index=1)

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

# -- ReBalancing
with st.expander("♻️ ReBalancing", expanded=True):
    rebalance_base_year = initial_date.year + 1
    rebalance_1_default = datetime(rebalance_base_year, 4, 1)
    rebalance_2_default = datetime(rebalance_base_year, 10, 1)

    rebalance_1 = st.checkbox("ReBalancing 1", value=True)
    rebalance_1_condition = st.checkbox("Warunek odchylenia wartości dla ReBalancing 1", value=False)
    rebalance_1_threshold = st.number_input("Próg odchylenia (%) dla ReBalancing 1", min_value=0.0, max_value=100.0, value=12.0, step=0.5)
    rebalance_1_start = st.date_input("Start ReBalancing 1", value=rebalance_1_default.date(), min_value=data.index.min().date(), max_value=data.index.max().date())

    rebalance_2 = st.checkbox("ReBalancing 2", value=False)
    rebalance_2_condition = st.checkbox("Warunek odchylenia wartości dla ReBalancing 2", value=False)
    rebalance_2_threshold = st.number_input("Próg odchylenia (%) dla ReBalancing 2", min_value=0.0, max_value=100.0, value=12.0, step=0.5)
    rebalance_2_start = st.date_input("Start ReBalancing 2", value=rebalance_2_default.date(), min_value=data.index.min().date(), max_value=data.index.max().date())

# -- Koszty magazynowania
with st.expander("📦 Koszty magazynowania"):
    storage_fee = st.number_input("Roczny koszt magazynowania (%)", value=1.5)
    vat = st.number_input("VAT (%)", value=19.0)
    storage_metal = st.selectbox(
        "Metal do pokrycia kosztów", 
        ["Gold", "Silver", "Platinum", "Palladium", "Best of year", "ALL"]
    )

# -- Marże i prowizje
with st.expander("📊 Marże i prowizje"):
    margins = {
        "Gold": st.number_input("Marża Gold (%)", value=15.6),
        "Silver": st.number_input("Marża Silver (%)", value=18.36),
        "Platinum": st.number_input("Marża Platinum (%)", value=24.24),
        "Palladium": st.number_input("Marża Palladium (%)", value=22.49)
    }

# -- Ceny odkupu i ceny ReBalancing
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






# =========================================
# 4. Funkcje pomocnicze do symulacji
# =========================================

def generate_purchase_dates(start_date, freq, day, end_date):
    dates = []
    current = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

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

    return [data.index[data.index.get_indexer([d], method="nearest")][0] for d in dates if len(data.index.get_indexer([d], method="nearest")) > 0]

def find_best_metal_of_year(start_date, end_date):
    start_prices = data.loc[start_date]
    end_prices = data.loc[end_date]
    growth = {}
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
        growth[metal] = (end_prices[metal + "_EUR"] / start_prices[metal + "_EUR"]) - 1
    return max(growth, key=growth.get)

# =========================================
# 5. Funkcja główna symulacji
# =========================================

def simulate(allocation):
    portfolio = {m: 0.0 for m in allocation}
    history = []
    invested = 0.0

    all_dates = data.loc[initial_date:end_purchase_date].index
    purchase_dates = generate_purchase_dates(initial_date, purchase_freq, purchase_day, end_purchase_date)

    last_year = None
    last_rebalance_dates = {
        "rebalance_1": None,
        "rebalance_2": None
    }

    def apply_rebalance(d, label, condition_enabled, threshold_percent):
        nonlocal last_rebalance_dates

        min_days_between_rebalances = 30

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

    # Początkowy zakup
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
            for metal, percent in allocation.items():
                price = prices[metal + "_EUR"] * (1 + margins[metal] / 100)
                grams = (purchase_amount * percent) / price
                portfolio[metal] += grams
            invested += purchase_amount
            actions.append("recurring")

        if rebalance_1 and d >= pd.to_datetime(rebalance_1_start) and d.month == rebalance_1_start.month and d.day == rebalance_1_start.day:
            actions.append(apply_rebalance(d, "rebalance_1", rebalance_1_condition, rebalance_1_threshold))

        if rebalance_2 and d >= pd.to_datetime(rebalance_2_start) and d.month == rebalance_2_start.month and d.day == rebalance_2_start.day:
            actions.append(apply_rebalance(d, "rebalance_2", rebalance_2_condition, rebalance_2_threshold))

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

    return df_result





# =========================================
# 6. Główna sekcja wyników symulacji
# =========================================

# 🚀 Uruchamiamy symulację tylko jeśli daty poprawne
if dates_valid:
    result = simulate(allocation)

    # 📈 Korekta wartości portfela o realną inflację
    inflation_dict = dict(zip(inflation_real["Rok"], inflation_real["Inflacja (%)"]))

    def calculate_cumulative_inflation(start_year, current_year):
        cumulative_factor = 1.0
        for year in range(start_year, current_year + 1):
            inflation = inflation_dict.get(year, 0.0) / 100
            cumulative_factor *= (1 + inflation)
        return cumulative_factor

    start_year = result.index.min().year
    real_values = []

    for date in result.index:
        nominal_value = result.loc[date, "Portfolio Value"]
        current_year = date.year
        cumulative_inflation = calculate_cumulative_inflation(start_year, current_year)
        real_value = nominal_value / cumulative_inflation if cumulative_inflation != 0 else nominal_value
        real_values.append(real_value)

    result["Portfolio Value Real"] = real_values

    # 📊 Wykres wartości portfela
    st.subheader(translations[language]["chart_subtitle"])

    result_plot = result.copy()
    result_plot["Storage Cost"] = 0.0

    storage_costs = result_plot[result_plot["Akcja"] == "storage_fee"].index
    for d in storage_costs:
        result_plot.at[d, "Storage Cost"] = result_plot.at[d, "Invested"] * (storage_fee / 100) * (1 + vat / 100)

    for col in ["Portfolio Value", "Portfolio Value Real", "Invested", "Storage Cost"]:
        result_plot[col] = pd.to_numeric(result_plot[col], errors="coerce").fillna(0)

    chart_data = result_plot[["Portfolio Value", "Portfolio Value Real", "Invested", "Storage Cost"]]

    chart_data.rename(columns={
        "Portfolio Value": f"💰 {translations[language]['portfolio_value']}",
        "Portfolio Value Real": f"🏛️ {translations[language]['real_portfolio_value']}",
        "Invested": f"💵 {translations[language]['invested']}",
        "Storage Cost": f"📦 {translations[language]['storage_cost']}"
    }, inplace=True)

    st.line_chart(chart_data)

    st.markdown("---")

    # 📊 Podsumowanie inwestycji
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

    st.metric("📈 Średnioroczna stopa zwrotu (CAGR)", f"{roczny_procent * 100:.2f}%")

    # 📈 Wzrosty metali
    st.subheader("📊 Wzrost cen metali od startu inwestycji")

    start_prices = data.loc[start_date]
    end_prices = data.loc[end_date]

    wzrosty = {}

    for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
        start_price = start_prices[metal + "_EUR"]
        end_price = end_prices[metal + "_EUR"]
        wzrost = (end_price / start_price - 1) * 100
        wzrosty[metal] = wzrost

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Złoto (Au)", f"{wzrosty['Gold']:.2f}%")
    with col2:
        st.metric("Srebro (Ag)", f"{wzrosty['Silver']:.2f}%")
    with col3:
        st.metric("Platyna (Pt)", f"{wzrosty['Platinum']:.2f}%")
    with col4:
        st.metric("Pallad (Pd)", f"{wzrosty['Palladium']:.2f}%")

    st.markdown("---")

    # ⚖️ Aktualne ilości gramów
    st.subheader("⚖️ Aktualne ilości metali (g)")

    aktualne_ilosci = {
        "Gold": result.iloc[-1]["Gold"],
        "Silver": result.iloc[-1]["Silver"],
        "Platinum": result.iloc[-1]["Platinum"],
        "Palladium": result.iloc[-1]["Palladium"]
    }

    kolory_metali = {
        "Gold": "#D4AF37",
        "Silver": "#C0C0C0",
        "Platinum": "#E5E4E2",
        "Palladium": "#CED0DD"
    }

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




# =========================================
# 7. Dodatkowe podsumowania i tabele
# =========================================

# 📅 Uproszczony podgląd: pierwszy dzień każdego roku
st.subheader("📅 Uproszczony podgląd: pierwszy dzień każdego roku")

result_filtered = result.groupby(result.index.year).first()

simple_table = pd.DataFrame({
    "Zainwestowane (EUR)": result_filtered["Invested"].round(0),
    "Wartość portfela (EUR)": result_filtered["Portfolio Value"].round(0),
    "Złoto (g)": result_filtered["Gold"].round(2),
    "Srebro (g)": result_filtered["Silver"].round(2),
    "Platyna (g)": result_filtered["Platinum"].round(2),
    "Pallad (g)": result_filtered["Palladium"].round(2),
    "Akcja": result_filtered["Akcja"]
})

simple_table["Zainwestowane (EUR)"] = simple_table["Zainwestowane (EUR)"].map(lambda x: f"{x:,.0f} EUR")
simple_table["Wartość portfela (EUR)"] = simple_table["Wartość portfela (EUR)"].map(lambda x: f"{x:,.0f} EUR")

# Mniejszy font w tabeli
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

st.markdown("---")

# 📦 Podsumowanie kosztów magazynowania
st.subheader("📦 Podsumowanie kosztów magazynowania")

storage_fees = result[result["Akcja"] == "storage_fee"]

total_storage_cost = storage_fees["Invested"].sum() * (storage_fee / 100) * (1 + vat / 100)

start_date = result.index.min()
end_date = result.index.max()
years = (end_date - start_date).days / 365.25

if years > 0:
    avg_annual_storage_cost = total_storage_cost / years
else:
    avg_annual_storage_cost = 0.0

last_storage_date = storage_fees.index.max()
if pd.notna(last_storage_date):
    last_storage_cost = result.loc[last_storage_date]["Invested"] * (storage_fee / 100) * (1 + vat / 100)
else:
    last_storage_cost = 0.0

current_portfolio_value = result["Portfolio Value"].iloc[-1]

if current_portfolio_value > 0:
    storage_cost_percentage = (last_storage_cost / current_portfolio_value) * 100
else:
    storage_cost_percentage = 0.0

col1, col2 = st.columns(2)
with col1:
    st.metric("Średnioroczny koszt magazynowania", f"{avg_annual_storage_cost:,.2f} EUR")
with col2:
    st.metric("Koszt magazynowania (% w ostatnim roku)", f"{storage_cost_percentage:.2f}%")

st.markdown("---")
