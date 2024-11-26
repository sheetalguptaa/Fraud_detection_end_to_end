import streamlit as st
import mysql.connector
import joblib  # Updated from pickle to joblib for better compatibility
import numpy as np

# Load the trained model
@st.cache_resource
def load_model():
    try:
        model = joblib.load("model.pkl")  # Updated to joblib
        return model
    except FileNotFoundError:
        st.error("Trained model file 'model.pkl' not found.")
        return None
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

# Function to connect to MySQL
def connect_to_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",       # Replace with your MySQL host
            user="root",            # Replace with your MySQL username
            password="password",    # Replace with your MySQL password
            database="FraudDetection"  # Replace with your database name
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# Function to insert data into the database
def insert_to_db(conn, data):
    try:
        cursor = conn.cursor()
        sql_query = """
        INSERT INTO Transactions (
            credit_limit, available_money, transaction_amount, current_balance, 
            card_present, expiration_date_key_in_match, money_left, 
            current_balance_percentage, credit_usage_ratio, transaction_to_balance_ratio, prediction
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(sql_query, data)
        conn.commit()
        cursor.close()
        st.success("Data successfully saved to the database.")
    except mysql.connector.Error as e:
        st.error(f"Error inserting data: {e}")

# Load the model
model = load_model()

# Add custom CSS for styling
st.markdown(
    """
    <style>
    body {
        background-image: url('https://www.transparenttextures.com/patterns/blueprint.png'); /* Background image */
        background-size: cover;
        color: #004d66; /* Text color */
    }
    .stButton>button {
        background-color: #007acc; /* Button color */
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 10px;
    }
    .stButton>button:hover {
        background-color: #005f99; /* Hover color */
    }
    h1, h3 {
        color: #004d66;
        text-align: center;
    }
    .stNumberInput, .stSelectbox {
        background-color: #e6f7ff;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit app
st.title("🌟 AI Fraud Detection System 🌟")
st.markdown("---")

# Create input fields
st.markdown("<h3>🔍 Enter Transaction Details Below:</h3>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    credit_limit = st.number_input("💳 Credit Limit", min_value=0.0, value=5000.0, step=0.01)
    transaction_amount = st.number_input("💰 Transaction Amount", min_value=0.0, value=100.0, step=0.01)
    available_money = st.number_input("🏦 Available Money", min_value=0.0, value=2000.0, step=0.01)
    card_present = st.selectbox("📇 Card Present", ["Yes", "No"])

with col2:
    current_balance = st.number_input("📊 Current Balance", min_value=0.0, value=1500.0, step=0.01)
    expiration_date_key_in_match = st.selectbox("⏳ Expiration Date Key-In Match", ["Yes", "No"])
    money_left = st.number_input("💵 Money Left (Available Money - Transaction Amount)", min_value=0.0, value=1900.0, step=0.01)
    current_balance_percentage = st.number_input("📈 Current Balance Percentage (Current Balance / Credit Limit)", min_value=0.0, value=0.3, step=0.01)

# Additional calculated features
credit_usage_ratio = st.number_input("📊 Credit Usage Ratio (Transaction Amount / Credit Limit)", min_value=0.0, value=0.02, step=0.01)
transaction_to_balance_ratio = st.number_input("📉 Transaction to Balance Ratio (Transaction Amount / Current Balance)", min_value=0.0, value=0.07, step=0.01)

# Convert categorical features to numeric
card_present_numeric = 1 if card_present == "Yes" else 0
expiration_date_key_in_match_numeric = 1 if expiration_date_key_in_match == "Yes" else 0

# Predict button
st.markdown("---")

if st.button("🔍 Predict"):
    if model:
        # Prepare input data
        input_data = np.array([[ 
            credit_limit, available_money, transaction_amount, current_balance,
            card_present_numeric, expiration_date_key_in_match_numeric,
            money_left, current_balance_percentage, credit_usage_ratio, transaction_to_balance_ratio
        ]])

        # Make prediction
        try:
            prediction = model.predict(input_data)
            result = "🛑 Fraudulent Transaction" if prediction[0] == 1 else "✅ Legitimate Transaction"

            # Display result
            st.success(f"Prediction: {result}")

            # Save to database
            conn = connect_to_db()
            if conn:
                db_data = (
                    credit_limit, available_money, transaction_amount, current_balance,
                    card_present_numeric, expiration_date_key_in_match_numeric,
                    money_left, current_balance_percentage, credit_usage_ratio, transaction_to_balance_ratio,
                    result
                )
                insert_to_db(conn, db_data)
                conn.close()
        except Exception as e:
            st.error(f"Error during prediction: {e}")
    else:
        st.error("Model not loaded. Please ensure 'model.pkl' is in the app directory.")
