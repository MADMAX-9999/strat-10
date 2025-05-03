import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go

# Global constants
GRAMS_IN_TROY_OUNCE = 31.1034768

# Page configuration
st.set_page_config(
    page_title="Strategia Majątku w Metalach", 
    page_icon="💰", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem 2rem;
    }
    .stSlider > div > div > div {
        background-color: #4CAF50;
    }
    .css-1v3fvcr {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Language selection function
def select_language():
    language = st.sidebar.selectbox("Wybierz język / Choose language", ("Polski", "English"))
    return language

# Function to create sample LBMA data if file doesn't exist
def create_sample_lbma_data():
    # Create sample data for demonstration
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date.today()
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # Create random-ish but realistic prices
    gold_base = 1000 + np.random.normal(0, 1, len(date_range)).cumsum() * 5
    silver_base = 15 + np.random.normal(0, 1, len(date_range)).cumsum() * 0.1
    platinum_base = 900 + np.random.normal(0, 1, len(date_range)).cumsum() * 4
    palladium_base = 1500 + np.random.normal(0, 1, len(date_range)).cumsum() * 6
    
    # Ensure prices are positive and have realistic relationships
    gold = np.maximum(800, gold_base)
    silver = np.maximum(5, silver_base)
    platinum = np.maximum(700, platinum_base)
    palladium = np.maximum(500, palladium_base)
    
    # Create DataFrame
    df = pd.DataFrame({
        'Date': date_range,
        'Gold': gold,
        'Silver': silver,
        'Platinum': platinum,
        'Palladium': palladium
    })
    
    return df

# Function to load metal prices
def load_metal_prices():
    # Try to load from uploaded file first
    uploaded_file = st.sidebar.file_uploader("Upload LBMA data (CSV format)", type=['csv'])
    
    if uploaded_file is not None:
        try:
            prices = pd.read_csv(uploaded_file, parse_dates=["Date"])
            st.sidebar.success("File successfully loaded!")
        except Exception as e:
            st.sidebar.error(f"Error loading file: {e}")
            st.sidebar.info("Using sample data instead.")
            prices = create_sample_lbma_data()
    else:
        # Try to load from local file
        try:
            prices = pd.read_csv("lbma_data.csv", parse_dates=["Date"])
            st.sidebar.info("Using local lbma_data.csv file.")
        except FileNotFoundError:
            st.sidebar.info("No local LBMA data file found. Using sample data for demonstration.")
            prices = create_sample_lbma_data()
        except Exception as e:
            st.sidebar.error(f"Error reading local file: {e}")
            st.sidebar.info("Using sample data instead.")
            prices = create_sample_lbma_data()
    
    # Standardize column names
    prices.columns = [col.strip().capitalize() for col in prices.columns]
    
    # Rename columns if needed
    column_map = {
        'Gold Am': 'Gold', 'Gold Pm': 'Gold', 'Gold': 'Gold',
        'Silver': 'Silver',
        'Platinum Am': 'Platinum', 'Platinum Pm': 'Platinum', 'Platinum': 'Platinum',
        'Palladium Am': 'Palladium', 'Palladium Pm': 'Palladium', 'Palladium': 'Palladium'
    }
    
    # Only map columns that exist
    valid_map = {k: v for k, v in column_map.items() if k in prices.columns}
    prices = prices.rename(columns=valid_map)
    
    # Ensure the DataFrame has the required columns
    required_cols = ['Date', 'Gold', 'Silver', 'Platinum', 'Palladium']
    missing_cols = [col for col in required_cols if col not in prices.columns]
    
    if 'Date' in missing_cols:
        st.error("Data must contain a 'Date' column.")
        return None
    
    # For any missing metal columns, create with NaN values
    for col in missing_cols:
        if col != 'Date':
            prices[col] = np.nan
            st.warning(f"Column '{col}' was missing and has been added with placeholder values.")
    
    # Set Date as index
    prices.set_index("Date", inplace=True)
    
    # Convert prices to numeric, coercing errors to NaN
    for col in ['Gold', 'Silver', 'Platinum', 'Palladium']:
        prices[col] = pd.to_numeric(prices[col], errors='coerce')
    
    # Forward fill missing values (use previous day's price)
    prices = prices.fillna(method='ffill')
    
    # If still any NaNs at the beginning, backward fill
    prices = prices.fillna(method='bfill')
    
    return prices

# Function to create sample inflation data
def create_sample_inflation_data(language):
    # Create sample data for demonstration
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date.today()
    date_range = pd.date_range(start=start_date, end=end_date, freq='M')
    
    # Create random-ish but realistic inflation data
    base_inflation = np.random.normal(0.2, 0.1, len(date_range)).cumsum()
    inflation_rate = 2 + base_inflation % 5  # Keep between 2-7%
    
    # Create DataFrame
    if language == "Polski":
        df = pd.DataFrame({
            'Data': date_range,
            'Inflacja (%)': inflation_rate
        })
        df.rename(columns={'Data': 'Date'}, inplace=True)
    else:
        df = pd.DataFrame({
            'Date': date_range,
            'Inflation (%)': inflation_rate
        })
    
    return df

# Function to load inflation data
def load_inflation(language):
    # Try to load from uploaded file first
    if language == "Polski":
        upload_label = "Wgraj dane inflacyjne (format CSV)"
        filename = "inflacja-PL.csv"
        col_name = "Inflacja (%)"
    else:
        upload_label = "Upload inflation data (CSV format)"
        filename = "inflacja-EN.csv"
        col_name = "Inflation (%)"
    
    uploaded_file = st.sidebar.file_uploader(upload_label, type=['csv'])
    
    if uploaded_file is not None:
        try:
            inflation = pd.read_csv(uploaded_file)
            st.sidebar.success("Inflation data successfully loaded!")
        except Exception as e:
            st.sidebar.error(f"Error loading inflation file: {e}")
            st.sidebar.info("Using sample inflation data instead.")
            inflation = create_sample_inflation_data(language)
    else:
        # Try to load from local file
        try:
            try:
                inflation = pd.read_csv(filename, encoding='utf-8')
            except UnicodeDecodeError:
                inflation = pd.read_csv(filename, encoding='cp1250')
            st.sidebar.info(f"Using local {filename} file.")
        except FileNotFoundError:
            st.sidebar.info(f"No local {filename} file found. Using sample data for demonstration.")
            inflation = create_sample_inflation_data(language)
        except Exception as e:
            st.sidebar.error(f"Error reading local inflation file: {e}")
            st.sidebar.info("Using sample inflation data instead.")
            inflation = create_sample_inflation_data(language)
    
    # Standardize column names
    if inflation.columns[0] != "Date":
        inflation.rename(columns={inflation.columns[0]: "Date"}, inplace=True)
    
    # Ensure we have the correct inflation column
    inflation_cols = [col for col in inflation.columns if "inf" in col.lower()]
    if inflation_cols:
        inflation.rename(columns={inflation_cols[0]: col_name}, inplace=True)
    elif len(inflation.columns) > 1:
        inflation.rename(columns={inflation.columns[1]: col_name}, inplace=True)
    else:
        st.error("Inflation data format is incorrect.")
        return None
    
    # Convert date to datetime
    inflation["Date"] = pd.to_datetime(inflation["Date"], errors='coerce')
    
    # Drop rows with invalid dates
    inflation = inflation.dropna(subset=["Date"])
    
    # Set Date as index
    inflation.set_index("Date", inplace=True)
    
    return inflation

# Helper function: find closest available prices
def get_next_available_price(prices, date):
    date_dt = pd.to_datetime(date)
    future_dates = prices.index[prices.index >= date_dt]
    
    if len(future_dates) == 0:
        # If no future dates, get the most recent price
        return prices.iloc[-1]
    
    for future_date in future_dates:
        row = prices.loc[future_date]
        if pd.notna(row["Gold"]):
            return row
    
    # If no valid prices found, return the first non-NaN row
    for idx, row in prices.iterrows():
        if pd.notna(row["Gold"]):
            return row
    
    # If still nothing found, return None
    return None

# Basic data form
def input_initial_data(prices, language):
    min_date = prices.index.min().date()
    max_date = prices.index.max().date()
    today = datetime.date.today()
    end_default = today if today <= max_date else max_date
    start_default = end_default - datetime.timedelta(days=365*5)  # Default 5 years
    if start_default < min_date:
        start_default = min_date

    if language == "Polski":
        st.sidebar.header("Dane podstawowe")
        amount = st.sidebar.number_input("Kwota początkowej alokacji (EUR)", min_value=0.0, step=1000.0, value=100000.0, format="%.2f")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Data pierwszego zakupu", value=start_default, min_value=min_date, max_value=max_date)
        with col2:
            end_date = st.date_input("Data ostatniego zakupu", value=end_default, min_value=min_date, max_value=max_date)

        st.sidebar.subheader("Zakupy systematyczne (transze odnawialne)")
        frequency = st.sidebar.selectbox("Periodyczność", ("Tygodniowa", "Miesięczna", "Kwartalna", "Roczna", "Jednorazowa"))
        
        # Default tranche based on frequency
        default_tranche = 250.0 if frequency == "Tygodniowa" else 1000.0 if frequency == "Miesięczna" else 3250.0 if frequency == "Kwartalna" else 10000.0 if frequency == "Roczna" else 0.0
        tranche_amount = st.sidebar.number_input("Kwota każdej transzy (EUR)", min_value=0.0, step=100.0, value=default_tranche, format="%.2f")
    else:
        st.sidebar.header("Basic Information")
        amount = st.sidebar.number_input("Initial Allocation Amount (EUR)", min_value=0.0, step=1000.0, value=100000.0, format="%.2f")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("First Purchase Date", value=start_default, min_value=min_date, max_value=max_date)
        with col2:
            end_date = st.date_input("Last Purchase Date", value=end_default, min_value=min_date, max_value=max_date)

        st.sidebar.subheader("Recurring Purchases (Renewable Tranches)")
        frequency = st.sidebar.selectbox("Frequency", ("Weekly", "Monthly", "Quarterly", "Annual", "One-time"))
        
        # Default tranche based on frequency
        default_tranche = 250.0 if frequency == "Weekly" else 1000.0 if frequency == "Monthly" else 3250.0 if frequency == "Quarterly" else 10000.0 if frequency == "Annual" else 0.0
        tranche_amount = st.sidebar.number_input("Amount of Each Tranche (EUR)", min_value=0.0, step=100.0, value=default_tranche, format="%.2f")

    st.sidebar.header("Koszt zakupu metali (%)")
    gold_markup = st.sidebar.number_input("Złoto (Gold) %", min_value=0.0, max_value=100.0, value=9.90, step=0.1, format="%.2f")
    silver_markup = st.sidebar.number_input("Srebro (Silver) %", min_value=0.0, max_value=100.0, value=13.5, step=0.1, format="%.2f")
    platinum_markup = st.sidebar.number_input("Platyna (Platinum) %", min_value=0.0, max_value=100.0, value=14.3, step=0.1, format="%.2f")
    palladium_markup = st.sidebar.number_input("Pallad (Palladium) %", min_value=0.0, max_value=100.0, value=16.9, step=0.1, format="%.2f")

    return amount, start_date, end_date, frequency, tranche_amount, gold_markup, silver_markup, platinum_markup, palladium_markup

# Strategy selection function
def select_strategy(language):
    if language == "Polski":
        st.sidebar.header("Wybór strategii")
        strategy = st.sidebar.radio("Wybierz strategię", ("FIXED", "DYNAMIC"))
    else:
        st.sidebar.header("Strategy Selection")
        strategy = st.sidebar.radio("Choose a strategy", ("FIXED", "DYNAMIC"))
    return strategy

# Function for setting proportions
def fixed_allocation(language):
    st.subheader("Ustaw proporcje metali / Set metal proportions")
    col1, col2 = st.columns(2)
    
    with col1:
        gold = st.slider("Złoto / Gold (%)", 0, 100, 40, step=5)
        silver = st.slider("Srebro / Silver (%)", 0, 100, 30, step=5)
    
    with col2:
        platinum = st.slider("Platyna / Platinum (%)", 0, 100, 15, step=5)
        palladium = st.slider("Pallad / Palladium (%)", 0, 100, 15, step=5)

    total = gold + silver + platinum + palladium
    
    # Display total with color coding
    if total == 100:
        st.success(f"**Suma / Total:** {total}% ✓")
    else:
        st.error(f"**Suma / Total:** {total}% ❌ (Musi być / Must be 100%)")
    
    return gold, silver, platinum, palladium

# Function for dynamic allocation strategy
def dynamic_allocation(language, prices):
    st.subheader("Dynamiczna alokacja / Dynamic allocation")
    st.write("Ta strategia zmienia alokację na podstawie stosunku cen metali do historycznej średniej.")
    st.write("This strategy changes allocation based on metal price ratios to historical averages.")
    
    # Calculate historical averages and standard deviations
    gold_mean = prices['Gold'].mean()
    silver_mean = prices['Silver'].mean()
    platinum_mean = prices['Platinum'].mean()
    palladium_mean = prices['Palladium'].mean()
    
    gold_std = prices['Gold'].std()
    silver_std = prices['Silver'].std()
    platinum_std = prices['Platinum'].std()
    palladium_std = prices['Palladium'].std()
    
    # Show current metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Gold średnia / mean", f"{gold_mean:.2f} EUR/oz")
        st.metric("Silver średnia / mean", f"{silver_mean:.2f} EUR/oz")
    with col2:
        st.metric("Platinum średnia / mean", f"{platinum_mean:.2f} EUR/oz")
        st.metric("Palladium średnia / mean", f"{palladium_mean:.2f} EUR/oz")
    
    # Allow user to adjust sensitivity
    sensitivity = st.slider("Czułość strategii / Strategy sensitivity", 0.5, 3.0, 1.0, 0.1)
    
    # Baseline allocation
    base_gold = st.slider("Bazowa alokacja złota / Base Gold allocation (%)", 0, 100, 40, step=5)
    base_silver = st.slider("Bazowa alokacja srebra / Base Silver allocation (%)", 0, 100, 30, step=5)
    base_platinum = st.slider("Bazowa alokacja platyny / Base Platinum allocation (%)", 0, 100, 15, step=5)
    base_palladium = st.slider("Bazowa alokacja palladu / Base Palladium allocation (%)", 0, 100, 15, step=5)
    
    total = base_gold + base_silver + base_platinum + base_palladium
    
    # Display total with color coding
    if total == 100:
        st.success(f"**Suma bazowa / Base Total:** {total}% ✓")
    else:
        st.error(f"**Suma bazowa / Base Total:** {total}% ❌ (Musi być / Must be 100%)")
    
    return base_gold, base_silver, base_platinum, base_palladium, sensitivity

# Simulation of FIXED strategy
def simulate_fixed_strategy(amount, start_date, end_date, frequency, tranche_amount,
                            gold_pct, silver_pct, platinum_pct, palladium_pct,
                            prices, gold_markup, silver_markup, platinum_markup, palladium_markup):
    # Map frequency string to pandas frequency code
    freq_map = {
        "Tygodniowa": "W", "Miesięczna": "M", "Kwartalna": "Q", "Roczna": "A", "Jednorazowa": None,
        "Weekly": "W", "Monthly": "M", "Quarterly": "Q", "Annual": "A", "One-time": None
    }
    
    # For one-time purchase, we only use the start date
    if freq_map.get(frequency) is None:
        schedule = pd.DatetimeIndex([pd.to_datetime(start_date)])
    else:
        # Create date range for purchases
        schedule = pd.date_range(start=start_date, end=end_date, freq=freq_map.get(frequency, "M"))
    
    # Initialize portfolio DataFrame
    portfolio = pd.DataFrame(index=schedule, columns=["Gold", "Silver", "Platinum", "Palladium", "Investment"]).fillna(0.0)
    
    # --- Initial investment ---
    initial_row = get_next_available_price(prices, start_date)
    if initial_row is not None:
        try:
            # Calculate spot prices per gram
            price_gold_g = initial_row["Gold"] / GRAMS_IN_TROY_OUNCE
            price_silver_g = initial_row["Silver"] / GRAMS_IN_TROY_OUNCE
            price_platinum_g = initial_row["Platinum"] / GRAMS_IN_TROY_OUNCE
            price_palladium_g = initial_row["Palladium"] / GRAMS_IN_TROY_OUNCE
            
            # Apply markup for purchase prices
            price_gold_g_buy = price_gold_g * (1 + gold_markup / 100)
            price_silver_g_buy = price_silver_g * (1 + silver_markup / 100)
            price_platinum_g_buy = price_platinum_g * (1 + platinum_markup / 100)
            price_palladium_g_buy = price_palladium_g * (1 + palladium_markup / 100)
            
            # Calculate grams purchased
            portfolio.loc[schedule[0], "Gold"] = (amount * gold_pct / 100) / price_gold_g_buy
            portfolio.loc[schedule[0], "Silver"] = (amount * silver_pct / 100) / price_silver_g_buy
            portfolio.loc[schedule[0], "Platinum"] = (amount * platinum_pct / 100) / price_platinum_g_buy
            portfolio.loc[schedule[0], "Palladium"] = (amount * palladium_pct / 100) / price_palladium_g_buy
            portfolio.loc[schedule[0], "Investment"] = amount
            
        except (KeyError, TypeError) as e:
            st.warning(f"Błąd podczas obliczania inwestycji początkowej: {e}")
    
    # --- Regular purchases (tranches) ---
    if freq_map.get(frequency) is not None:  # Skip for one-time purchases
        for i, date in enumerate(schedule):
            if i == 0:  # Skip first date (initial investment already made)
                continue
                
            row = get_next_available_price(prices, date)
            if row is not None:
                try:
                    # Calculate spot prices per gram
                    price_gold_g = row["Gold"] / GRAMS_IN_TROY_OUNCE
                    price_silver_g = row["Silver"] / GRAMS_IN_TROY_OUNCE
                    price_platinum_g = row["Platinum"] / GRAMS_IN_TROY_OUNCE
                    price_palladium_g = row["Palladium"] / GRAMS_IN_TROY_OUNCE
                    
                    # Apply markup for purchase prices
                    price_gold_g_buy = price_gold_g * (1 + gold_markup / 100)
                    price_silver_g_buy = price_silver_g * (1 + silver_markup / 100)
                    price_platinum_g_buy = price_platinum_g * (1 + platinum_markup / 100)
                    price_palladium_g_buy = price_palladium_g * (1 + palladium_markup / 100)
                    
                    # Calculate grams purchased for each tranche
                    portfolio.loc[date, "Gold"] = (tranche_amount * gold_pct / 100) / price_gold_g_buy
                    portfolio.loc[date, "Silver"] = (tranche_amount * silver_pct / 100) / price_silver_g_buy
                    portfolio.loc[date, "Platinum"] = (tranche_amount * platinum_pct / 100) / price_platinum_g_buy
                    portfolio.loc[date, "Palladium"] = (tranche_amount * palladium_pct / 100) / price_palladium_g_buy
                    portfolio.loc[date, "Investment"] = tranche_amount
                    
                except (KeyError, TypeError) as e:
                    st.warning(f"Błąd podczas obliczania transzy dla {date}: {e}")
    
    # Calculate cumulative amounts
    cumulative = portfolio.cumsum()
    
    # Add total investment
    cumulative["Total Investment"] = cumulative["Investment"]
    
    # Calculate allocation percentages for reporting
    for date in cumulative.index:
        total_grams = (
            cumulative.loc[date, "Gold"] + 
            cumulative.loc[date, "Silver"] + 
            cumulative.loc[date, "Platinum"] + 
            cumulative.loc[date, "Palladium"]
        )
        if total_grams > 0:
            cumulative.loc[date, "Gold_Pct"] = (cumulative.loc[date, "Gold"] / total_grams) * 100
            cumulative.loc[date, "Silver_Pct"] = (cumulative.loc[date, "Silver"] / total_grams) * 100
            cumulative.loc[date, "Platinum_Pct"] = (cumulative.loc[date, "Platinum"] / total_grams) * 100
            cumulative.loc[date, "Palladium_Pct"] = (cumulative.loc[date, "Palladium"] / total_grams) * 100
    
    return cumulative

# Simulate DYNAMIC strategy
def simulate_dynamic_strategy(amount, start_date, end_date, frequency, tranche_amount,
                              base_gold, base_silver, base_platinum, base_palladium, sensitivity,
                              prices, gold_markup, silver_markup, platinum_markup, palladium_markup):
    # Map frequency string to pandas frequency code
    freq_map = {
        "Tygodniowa": "W", "Miesięczna": "M", "Kwartalna": "Q", "Roczna": "A", "Jednorazowa": None,
        "Weekly": "W", "Monthly": "M", "Quarterly": "Q", "Annual": "A", "One-time": None
    }
    
    # For one-time purchase, we only use the start date
    if freq_map.get(frequency) is None:
        schedule = pd.DatetimeIndex([pd.to_datetime(start_date)])
    else:
        # Create date range for purchases
        schedule = pd.date_range(start=start_date, end=end_date, freq=freq_map.get(frequency, "M"))
    
    # Initialize portfolio DataFrame
    portfolio = pd.DataFrame(index=schedule, columns=["Gold", "Silver", "Platinum", "Palladium", 
                                                     "Gold_Pct", "Silver_Pct", "Platinum_Pct", "Palladium_Pct",
                                                     "Investment"]).fillna(0.0)
    
    # Calculate moving averages and standard deviations
    window = 252  # Approximately 1 year of trading days
    prices_copy = prices.copy()
    
    # Calculate historical statistics (we need this available for the whole timeseries)
    prices_copy['Gold_MA'] = prices_copy['Gold'].rolling(window=window, min_periods=1).mean()
    prices_copy['Silver_MA'] = prices_copy['Silver'].rolling(window=window, min_periods=1).mean()
    prices_copy['Platinum_MA'] = prices_copy['Platinum'].rolling(window=window, min_periods=1).mean()
    prices_copy['Palladium_MA'] = prices_copy['Palladium'].rolling(window=window, min_periods=1).mean()
    
    prices_copy['Gold_STD'] = prices_copy['Gold'].rolling(window=window, min_periods=1).std()
    prices_copy['Silver_STD'] = prices_copy['Silver'].rolling(window=window, min_periods=1).std()
    prices_copy['Platinum_STD'] = prices_copy['Platinum'].rolling(window=window, min_periods=1).std()
    prices_copy['Palladium_STD'] = prices_copy['Palladium'].rolling(window=window, min_periods=1).std()
    
    # --- Initial investment ---
    initial_row = get_next_available_price(prices, start_date)
    if initial_row is not None:
        try:
            # Get corresponding row from prices_copy with stats
            stats_date = pd.to_datetime(start_date)
            # Find closest date
            closest_date = prices_copy.index[prices_copy.index >= stats_date][0]
            stats_row = prices_copy.loc[closest_date]
            
            # Calculate Z-scores
            gold_zscore = (initial_row["Gold"] - stats_row["Gold_MA"]) / stats_row["Gold_STD"] if stats_row["Gold_STD"] > 0 else 0
            silver_zscore = (initial_row["Silver"] - stats_row["Silver_MA"]) / stats_row["Silver_STD"] if stats_row["Silver_STD"] > 0 else 0
            platinum_zscore = (initial_row["Platinum"] - stats_row["Platinum_MA"]) / stats_row["Platinum_STD"] if stats_row["Platinum_STD"] > 0 else 0
            palladium_zscore = (initial_row["Palladium"] - stats_row["Palladium_MA"]) / stats_row["Palladium_STD"] if stats_row["Palladium_STD"] > 0 else 0
            
            # Adjust allocation percentages based on Z-scores (negative Z-score means price is below average, buy more)
            gold_pct = base_gold * (1 - sensitivity * gold_zscore/3)
            silver_pct = base_silver * (1 - sensitivity * silver_zscore/3)
            platinum_pct = base_platinum * (1 - sensitivity * platinum_zscore/3)
            palladium_pct = base_palladium * (1 - sensitivity * palladium_zscore/3)
            
            # Ensure no negative percentages
            gold_pct = max(0, gold_pct)
            silver_pct = max(0, silver_pct)
            platinum_pct = max(0, platinum_pct)
            palladium_pct = max(0, palladium_pct)
            
            # Normalize to sum to 100%
            total = gold_pct + silver_pct + platinum_pct + palladium_pct
            if total > 0:
                gold_pct = (gold_pct / total) * 100
                silver_pct = (silver_pct / total) * 100
                platinum_pct = (platinum_pct / total) * 100
                palladium_pct = (palladium_pct / total) * 100
            else:
                # Fallback to base percentages if something went wrong
                gold_pct = base_gold
                silver_pct = base_silver
                platinum_pct = base_platinum
                palladium_pct = base_palladium
            
            # Store the percentages
            portfolio.loc[schedule[0], "Gold_Pct"] = gold_pct
            portfolio.loc[schedule[0], "Silver_Pct"] = silver_pct
            portfolio.loc[schedule[0], "Platinum_Pct"] = platinum_pct
            portfolio.loc[schedule
