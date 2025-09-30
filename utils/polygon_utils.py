"""
Polygon.io API utilities for stock data retrieval
Alternative to Yahoo Finance with better rate limits
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '3lKo1IgQ3hXMjMCkmbQACTJySZHkfld7')
POLYGON_BASE_URL = 'https://api.polygon.io'


def get_polygon_stock_info(ticker):
    """
    Get comprehensive stock information from Polygon.io
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Stock information including price, fundamentals, and company details
    """
    try:
        ticker = ticker.upper().strip()
        
        # Get current quote
        quote_url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/prev"
        quote_params = {'apikey': POLYGON_API_KEY}
        
        quote_response = requests.get(quote_url, params=quote_params)
        
        if quote_response.status_code == 429:
            return {
                'ticker': ticker,
                'name': ticker,
                'error': f'Rate limited by Polygon API. Status: {quote_response.status_code}'
            }
        
        if quote_response.status_code != 200:
            return {
                'ticker': ticker,
                'name': ticker,
                'error': f'Polygon API error: {quote_response.status_code} - {quote_response.text}'
            }
        
        quote_data = quote_response.json()
        
        # Get ticker details
        details_url = f"{POLYGON_BASE_URL}/v3/reference/tickers/{ticker}"
        details_params = {'apikey': POLYGON_API_KEY}
        
        details_response = requests.get(details_url, params=details_params)
        details_data = details_response.json() if details_response.status_code == 200 else {}
        
        # Extract quote information
        results = quote_data.get('results', [])
        if not results:
            return {
                'ticker': ticker,
                'name': ticker,
                'error': 'No price data available from Polygon'
            }
        
        latest_quote = results[0]
        
        # Extract company details
        ticker_details = details_data.get('results', {})
        
        # Calculate basic metrics
        current_price = latest_quote.get('c')  # Close price
        open_price = latest_quote.get('o')     # Open price
        high_price = latest_quote.get('h')     # High price
        low_price = latest_quote.get('l')      # Low price
        volume = latest_quote.get('v')         # Volume
        
        # Build comprehensive stock info
        stock_info = {
            'ticker': ticker,
            'name': ticker_details.get('name', ticker),
            'current_price': current_price,
            'open_price': open_price,
            'high_price': high_price,
            'low_price': low_price,
            'volume': volume,
            'market_cap': ticker_details.get('market_cap'),
            'sector': ticker_details.get('sic_description'),
            'industry': ticker_details.get('sic_description'),
            'country': ticker_details.get('locale', 'US'),
            'currency': ticker_details.get('currency_name', 'USD'),
            'exchange': ticker_details.get('primary_exchange'),
            'website': ticker_details.get('homepage_url'),
            'description': ticker_details.get('description'),
            'employees': None,  # Not available in basic Polygon data
            'pe_ratio': None,   # Would need additional API calls
            'dividend_yield': None,  # Would need additional API calls
            'data_source': 'Polygon.io',
            'last_updated': datetime.now().isoformat()
        }
        
        return stock_info
        
    except requests.exceptions.RequestException as e:
        return {
            'ticker': ticker,
            'name': ticker,
            'error': f'Network error accessing Polygon API: {str(e)}'
        }
    except Exception as e:
        return {
            'ticker': ticker,
            'name': ticker,
            'error': f'Error processing Polygon data: {str(e)}'
        }


def get_polygon_historical_data(ticker, days=30):
    """
    Get historical price data from Polygon.io
    
    Args:
        ticker (str): Stock ticker symbol
        days (int): Number of days of historical data
        
    Returns:
        pd.DataFrame: Historical price data
    """
    try:
        ticker = ticker.upper().strip()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Format dates for API
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Get historical data
        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start_str}/{end_str}"
        params = {
            'apikey': POLYGON_API_KEY,
            'adjusted': 'true',
            'sort': 'asc'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            return pd.DataFrame()  # Return empty DataFrame on error
        
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Convert timestamp to datetime
        df['date'] = pd.to_datetime(df['t'], unit='ms')
        
        # Rename columns to standard format
        df = df.rename(columns={
            'o': 'open',
            'h': 'high', 
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        })
        
        # Select and reorder columns
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df = df.set_index('date')
        
        return df
        
    except Exception as e:
        print(f"Error getting historical data: {e}")
        return pd.DataFrame()


def test_polygon_connection():
    """
    Test Polygon.io API connection and key validity
    
    Returns:
        dict: Connection test results
    """
    try:
        # Test with a simple API call
        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/AAPL/prev"
        params = {'apikey': POLYGON_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        
        result = {
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'api_key_valid': POLYGON_API_KEY is not None and len(POLYGON_API_KEY) > 10,
            'response_time_ms': response.elapsed.total_seconds() * 1000,
            'timestamp': datetime.now().isoformat()
        }
        
        if response.status_code == 200:
            data = response.json()
            result['sample_data'] = data.get('results', [])[:1]  # First result only
        else:
            result['error'] = response.text
            
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'api_key_valid': POLYGON_API_KEY is not None and len(POLYGON_API_KEY) > 10,
            'timestamp': datetime.now().isoformat()
        }


def get_polygon_market_status():
    """
    Get current market status from Polygon.io
    
    Returns:
        dict: Market status information
    """
    try:
        url = f"{POLYGON_BASE_URL}/v1/marketstatus/now"
        params = {'apikey': POLYGON_API_KEY}
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'error': f'Market status API error: {response.status_code}',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            'error': f'Error getting market status: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the Polygon API connection
    print("Testing Polygon.io API connection...")
    test_result = test_polygon_connection()
    print(f"Connection test: {test_result}")
    
    if test_result['success']:
        print("\nTesting stock info retrieval...")
        stock_info = get_polygon_stock_info('AAPL')
        print(f"AAPL info: {stock_info}")
        
        print("\nTesting historical data...")
        hist_data = get_polygon_historical_data('AAPL', days=5)
        print(f"Historical data shape: {hist_data.shape}")
        if not hist_data.empty:
            print(hist_data.head())
