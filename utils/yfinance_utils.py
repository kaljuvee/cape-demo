"""
YFinance utility functions for CAPE calculation
Developed by Lohusalu Capital Management
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import sqlite3
import os

# Caveats as comments:
# - yfinance earnings data is trailing twelve months and not CPI-adjusted; 
#   for full rigor you would download company 10-K EPS and CPI-deflate yourself.
# - Survivorship bias: the notebook uses today's 500 names for the entire history. 
#   To be perfect you need the historical membership (S&P provides this commercially, 
#   or you can scrape it from Siblis Research).
# - Rebalancing: the equal-weight index is rebalanced quarterly; the script above is monthly. 
#   Switch to quarterly if you want to match the S&P 500 Equal Weight Index methodology exactly.

def get_shiller_data():
    """
    Download Robert Shiller's monthly S&P real-EPS data from Yale Economics
    Returns: DataFrame with Date index and columns for Price, E10_real
    """
    try:
        url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
        shiller = (
            pd.read_excel(url, sheet_name="Data", skiprows=7, usecols="A,D,E")
            .rename(columns={"Unnamed: 0": "Date", "P": "Price", "E10": "E10_real"})
            .dropna()
        )
        shiller["Date"] = pd.to_datetime(shiller["Date"], format="%Y.%m")
        shiller = shiller.set_index("Date").sort_index()
        return shiller
    except Exception as e:
        print(f"Error downloading Shiller data: {e}")
        return None

def get_sp500_tickers():
    """
    Get current S&P 500 constituent tickers from Wikipedia
    Returns: List of ticker symbols
    """
    try:
        # Add headers to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        wiki = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", 
                           attrs={'class': 'wikitable sortable'})[0]
        tickers = sorted(wiki["Symbol"].str.replace(".", "-", regex=False).tolist())
        return tickers
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        # Return a fallback list of major S&P 500 tickers for demo purposes
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'UNH', 'JNJ',
            'V', 'PG', 'JPM', 'HD', 'CVX', 'MA', 'BAC', 'ABBV', 'PFE', 'AVGO',
            'KO', 'MRK', 'COST', 'PEP', 'TMO', 'WMT', 'CSCO', 'ACN', 'DIS', 'ABT',
            'VZ', 'ADBE', 'NFLX', 'CRM', 'NKE', 'INTC', 'T', 'CMCSA', 'XOM', 'DHR',
            'QCOM', 'TXN', 'BMY', 'PM', 'RTX', 'SPGI', 'NEE', 'UNP', 'LOW', 'HON'
        ]

def download_stock_data(tickers, years_back=12):
    """
    Download historical stock price and earnings data
    Args:
        tickers: List of ticker symbols
        years_back: Number of years of historical data to fetch
    Returns: Tuple of (prices DataFrame, earnings DataFrame)
    """
    try:
        start_date = f"{datetime.now().year - years_back}-01-01"
        
        # Download adjusted close prices
        prices = yf.download(tickers, start=start_date, interval="1mo")["Adj Close"]
        
        # Download earnings data (this might not work as expected with yfinance)
        # Using a proxy approach with financial data
        earnings_data = {}
        for ticker in tickers[:10]:  # Limit to first 10 for demo purposes
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                if 'trailingEps' in info and info['trailingEps'] is not None:
                    earnings_data[ticker] = info['trailingEps']
            except:
                continue
        
        # Create a simple earnings DataFrame (this is a simplified approach)
        earnings = pd.DataFrame(index=prices.index)
        for ticker in earnings_data:
            earnings[ticker] = earnings_data[ticker]
        
        return prices, earnings
    except Exception as e:
        print(f"Error downloading stock data: {e}")
        return None, None

def calculate_individual_cape(prices, earnings, date):
    """
    Calculate CAPE for individual stocks at a specific date
    Args:
        prices: DataFrame of stock prices
        earnings: DataFrame of stock earnings
        date: Date for calculation
    Returns: Series of individual CAPE ratios
    """
    try:
        # Get prices for this date
        p = prices.loc[date] if date in prices.index else prices.iloc[-1]
        
        # Calculate 10-year average earnings (120 months, allowing NaNs)
        end_idx = prices.index.get_loc(date) if date in prices.index else len(prices) - 1
        start_idx = max(0, end_idx - 119)  # 120 months = 10 years
        
        e10 = earnings.iloc[start_idx:end_idx+1].mean()
        
        # Calculate individual CAPEs
        cape = p / e10
        
        return cape.dropna()
    except Exception as e:
        print(f"Error calculating individual CAPE: {e}")
        return pd.Series()

def calculate_equal_weight_cape(prices, earnings):
    """
    Calculate equal-weight CAPE series over time
    Args:
        prices: DataFrame of stock prices
        earnings: DataFrame of stock earnings
    Returns: Series of equal-weight CAPE values
    """
    try:
        # Use last 5 years for demo (monthly frequency)
        start_date = datetime.now() - timedelta(days=5*365)
        idx = pd.date_range(start_date, datetime.now(), freq="M")
        
        ew_cape_data = {}
        for date in idx:
            if date <= prices.index[-1]:
                cape_values = calculate_individual_cape(prices, earnings, date)
                if len(cape_values) > 0:
                    ew_cape_data[date] = cape_values.mean()
        
        return pd.Series(ew_cape_data, name="Equal_Weight_CAPE")
    except Exception as e:
        print(f"Error calculating equal-weight CAPE: {e}")
        return pd.Series()

def search_ticker(query):
    """
    Search for ticker symbols based on company name or ticker
    Args:
        query: Search string
    Returns: List of matching tickers with company names
    """
    try:
        tickers = get_sp500_tickers()
        matches = []
        
        # Simple search - in a real implementation, you'd want more sophisticated matching
        for ticker in tickers:
            if query.upper() in ticker.upper():
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    company_name = info.get('longName', ticker)
                    matches.append({'ticker': ticker, 'name': company_name})
                except:
                    matches.append({'ticker': ticker, 'name': ticker})
        
        return matches[:10]  # Return top 10 matches
    except Exception as e:
        print(f"Error searching tickers: {e}")
        return []

def get_stock_info(ticker):
    """
    Get detailed information for a specific stock
    Args:
        ticker: Stock ticker symbol
    Returns: Dictionary with stock information
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        
        return {
            'ticker': ticker,
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'current_price': hist['Close'].iloc[-1] if len(hist) > 0 else None,
            'pe_ratio': info.get('trailingPE', None),
            'market_cap': info.get('marketCap', None),
            'dividend_yield': info.get('dividendYield', None)
        }
    except Exception as e:
        print(f"Error getting stock info for {ticker}: {e}")
        return {'ticker': ticker, 'name': ticker, 'error': str(e)}

def calculate_cape_comparison():
    """
    Calculate and compare cap-weight vs equal-weight CAPE
    Returns: DataFrame with both series
    """
    try:
        # Get Shiller data for cap-weight CAPE
        shiller = get_shiller_data()
        if shiller is None:
            return None
        
        # Get S&P 500 data for equal-weight CAPE
        tickers = get_sp500_tickers()
        prices, earnings = download_stock_data(tickers[:50])  # Limit for demo
        
        if prices is None or earnings is None:
            return None
        
        # Calculate equal-weight CAPE
        ew_cape = calculate_equal_weight_cape(prices, earnings)
        
        # Combine the series
        comparison = pd.concat([
            shiller["E10_real"].rename("Cap_Weight_CAPE_Shiller"),
            ew_cape
        ], axis=1).dropna()
        
        return comparison
    except Exception as e:
        print(f"Error calculating CAPE comparison: {e}")
        return None
