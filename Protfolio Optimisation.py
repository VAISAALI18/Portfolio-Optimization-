import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from collections import deque

# TreeNode class for BST
class TreeNode:
    def __init__(self, symbol, expected_return, risk):
        self.symbol = symbol
        self.expected_return = expected_return
        self.risk = risk
        self.left = None
        self.right = None

# Function to download stock data
def download_stock_data(symbols, start_date, end_date):
    all_data = {}
    for symbol in symbols:
        try:
            data = yf.download(symbol, start=start_date, end=end_date)
            all_data[symbol] = data
        except Exception as e:
            st.error(f"Error occurred while downloading data for {symbol}: {e}")
    return all_data

# Function to calculate metrics (expected return and risk)
def calculate_metrics(data):
    daily_returns = data['Adj Close'].pct_change()
    expected_return = daily_returns.mean()
    risk = daily_returns.std()
    return expected_return.item(), risk.item()  # Ensure scalar values

# Fractional knapsack function
def fractional_knapsack(values, weights, capacity):
    index = list(range(len(values)))
    ratio = [v / w for v, w in zip(values, weights)]
    index.sort(key=lambda i: ratio[i], reverse=True)

    max_value = 0
    fractions = [0] * len(values)
    for i in index:
        if weights[i] <= capacity:
            fractions[i] = 1
            max_value += values[i]
            capacity -= weights[i]
        else:
            fractions[i] = capacity / weights[i]
            max_value += values[i] * fractions[i]
            break

    return max_value, fractions

# Function to insert nodes into BST
def insert(root, symbol, expected_return, risk):
    if root is None:
        return TreeNode(symbol, expected_return, risk)
    if float(expected_return) > float(root.expected_return):  # Force float comparison
        root.right = insert(root.right, symbol, expected_return, risk)
    else:
        root.left = insert(root.left, symbol, expected_return, risk)
    return root

# Merge sort BST to sort companies by expected return
def merge_sort_bst(root, descending=True):
    def inorder_traversal(node):
        if node:
            inorder_traversal(node.right if descending else node.left)
            symbols.append(node.symbol)
            returns.append(node.expected_return)
            risks.append(node.risk)
            inorder_traversal(node.left if descending else node.right)
    
    symbols, returns, risks = [], [], []
    inorder_traversal(root)
    return symbols, returns, risks

# Streamlit UI
st.title("Stock Portfolio Optimization")

# Input parameters
symbols_list = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "TSLA", "V", "JNJ",
    "WMT", "JPM", "MA", "PG", "NVDA", "HD", "PYPL", "DIS", "VZ", "KO",
    "NFLX", "PFE", "MRK", "T", "PEP", "INTC", "CMCSA", "XOM", "NKE", "CSCO",
    "ABT", "ABBV", "ORCL", "ACN", "CVX", "MDT", "UNH", "IBM", "QCOM", "COST",
    "HON", "MCD", "CAT", "MMM", "TXN", "GILD", "BA", "LLY", "AMGN", "SBUX"
]

symbols = st.multiselect("Select Company Symbols", symbols_list, default=["AAPL", "MSFT", "AMZN", "GOOGL"])
start_date = st.date_input("Start Date", value=pd.to_datetime("2023-05-10"))
end_date = st.date_input("End Date", value=pd.to_datetime("2024-05-10"))
risk_free_rate = st.number_input("Risk-Free Rate", value=0.05)
max_risk_capacity = st.number_input("Maximum Risk Capacity", value=0.04)

# Download data for all symbols
if st.button("Download Data"):
    all_stock_data = download_stock_data(symbols, start_date, end_date)

    # Create a BST based on expected returns
    root = None
    for symbol, data in all_stock_data.items():
        if not data.empty:
            expected_return, risk = calculate_metrics(data)
            root = insert(root, symbol, expected_return, risk)
        else:
            st.warning(f"No data available for {symbol}")

    # Calculate metrics for each company
    values = []
    weights = []
    metrics = {}

    for symbol, data in all_stock_data.items():
        if not data.empty:
            expected_return, risk = calculate_metrics(data)
            values.append(expected_return)
            weights.append(risk)

            sharpe_ratio = (expected_return - risk_free_rate) / risk
            beta = 1  # Assuming a beta of 1 for simplicity
            treynor_ratio = (expected_return - risk_free_rate) / beta

            metrics[symbol] = {
                'Expected Return': expected_return,
                'Risk': risk,
                'Sharpe Ratio': sharpe_ratio,
                'Treynor Ratio': treynor_ratio
            }

    # Display metrics if calculated
    if metrics:
        metrics_df = pd.DataFrame(metrics).T

        fig, axes = plt.subplots(2, 2, figsize=(14, 16))
        metrics_df['Expected Return'].plot(kind='bar', ax=axes[0, 0], color='b', title='Expected Return')
        metrics_df['Risk'].plot(kind='bar', ax=axes[0, 1], color='r', title='Risk (Volatility)')
        metrics_df['Sharpe Ratio'].plot(kind='bar', ax=axes[1, 0], color='g', title='Sharpe Ratio')
        metrics_df['Treynor Ratio'].plot(kind='bar', ax=axes[1, 1], color='purple', title='Treynor Ratio')

        st.pyplot(fig)

    # Sort the BST
    sorted_symbols, sorted_returns, sorted_risks = merge_sort_bst(root, descending=True)

    # Display sorted symbols based on Expected Return
    st.subheader("Companies sorted by Expected Return:")
    for symbol, ret, risk in zip(sorted_symbols, sorted_returns, sorted_risks):
        st.write(f"{symbol} - Expected Return: {ret:.4f}, Risk: {risk:.4f}")

    # Apply Fractional Knapsack
    max_return, fractions = fractional_knapsack(sorted_returns, sorted_risks, max_risk_capacity)

    # Display the results
    st.subheader("Selected Companies and Fractions:")
    for i, symbol in enumerate(sorted_symbols):
        if fractions[i] > 0:
            st.write(f"{symbol} - Fraction: {fractions[i]:.4f}")

    st.write(f"Maximum Expected Return: {max_return:.4f}")
