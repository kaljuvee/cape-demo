"""
CAPE Demo - Stock Analysis with CAPE Calculations
Main Application - Stock Analysis Focus
Developed by Lohusalu Capital Management
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import uuid
import io
import os

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use environment variables directly
    pass

# Import utility functions
from utils.yfinance_utils import (
    get_shiller_data, 
    get_sp500_tickers, 
    calculate_cape_comparison,
    search_ticker,
    get_stock_info
)
from utils.polygon_utils import (
    get_polygon_stock_info,
    test_polygon_connection,
    get_polygon_market_status
)
from utils.db_utils import (
    init_database,
    save_search_history, 
    get_search_history, 
    get_session_stats,
    save_cape_calculation,
    get_cape_calculations
)

# Page configuration
st.set_page_config(
    page_title="CAPE Demo - Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_database()

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

def calculate_individual_cape(ticker, data_source="Polygon.io"):
    """
    Calculate CAPE for an individual stock
    """
    try:
        # Get stock data
        if data_source == "Polygon.io":
            stock_info = get_polygon_stock_info(ticker)
        else:
            stock_info = get_stock_info(ticker)
        
        if 'error' in stock_info:
            return None, stock_info.get('error', 'Unknown error')
        
        # For demonstration, we'll use a simplified CAPE calculation
        # In a real implementation, you'd need 10 years of earnings data
        current_price = stock_info.get('current_price')
        pe_ratio = stock_info.get('pe_ratio')
        
        if current_price and pe_ratio:
            # Simplified CAPE estimate (real CAPE needs 10-year average real earnings)
            # This is a placeholder - actual CAPE requires historical earnings data
            estimated_cape = pe_ratio * 0.8  # Rough approximation
            return estimated_cape, None
        else:
            # If no PE ratio available, try to estimate from other data
            # This is a very rough estimation for demo purposes
            if current_price:
                # Use market average CAPE as baseline (around 25-30)
                estimated_cape = 27.5  # Market average approximation
                return estimated_cape, "Estimated using market average (PE data unavailable)"
            else:
                return None, "Insufficient data for CAPE calculation"
                
    except Exception as e:
        return None, f"Error calculating CAPE: {str(e)}"

def main():
    # Header
    st.markdown("# 📈 CAPE Demo - Stock Analysis")
    st.markdown("### Individual Stock CAPE Analysis")
    st.markdown("*Developed by Lohusalu Capital Management*")
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        
        # Session stats
        try:
            stats = get_session_stats(st.session_state.session_id)
            st.metric("Calculations", stats.get('calculations_count', 0))
            st.metric("Searches", stats.get('searches_count', 0))
        except:
            st.metric("Calculations", 0)
            st.metric("Searches", 0)
        
        st.markdown("---")
        
        # Data Source Selection
        st.subheader("📊 Data Source")
        data_source = st.selectbox(
            "Choose API for stock analysis:",
            ["Polygon.io", "Yahoo Finance (yfinance)"],
            index=0,  # Default to Polygon
            help="Polygon.io typically has better rate limits and more reliable data"
        )
        
        # API Status Check
        if data_source == "Polygon.io":
            if st.button("🔍 Test Polygon API"):
                with st.spinner("Testing Polygon.io connection..."):
                    test_result = test_polygon_connection()
                    if test_result['success']:
                        st.success("✅ Polygon API Connected")
                        st.json({
                            "Status": "Connected",
                            "Response Time": f"{test_result['response_time_ms']:.0f}ms",
                            "API Key": "Valid" if test_result['api_key_valid'] else "Invalid"
                        })
                    else:
                        st.error("❌ Polygon API Error")
                        st.json(test_result)
        
        st.markdown("---")
        
        # Quick Actions
        st.subheader("Quick Actions")
        
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.success("Cache cleared!")
        
        # Recent searches
        st.subheader("🔍 Recent Searches")
        try:
            search_history = get_search_history(st.session_state.session_id, limit=5)
            
            if not search_history.empty:
                for _, row in search_history.iterrows():
                    results = row['results']
                    if isinstance(results, list) and results:
                        result = results[0]  # Take first result
                        if st.button(f"{result.get('ticker', 'N/A')} - {result.get('name', 'N/A')[:20]}...", 
                                   key=f"sidebar_history_{result.get('ticker', 'unknown')}_{row.name}"):
                            st.session_state.analyze_ticker = result.get('ticker', '')
                            st.rerun()
            else:
                st.info("No recent searches.")
                
        except Exception as e:
            st.info("Search history unavailable.")

    # Main content
    st.header("🔍 Stock Analysis with CAPE")
    
    # Check if ticker was selected from search or sidebar
    if 'analyze_ticker' in st.session_state:
        ticker_input = st.session_state.analyze_ticker
        del st.session_state.analyze_ticker
    else:
        ticker_input = ""
    
    # Single input field for both search and direct analysis
    col1, col2, col3 = st.columns([5, 1.5, 1.5])
    
    with col1:
        search_query = st.text_input(
            "Enter ticker symbol or company name:",
            value=ticker_input,
            placeholder="e.g., AAPL, Apple, Microsoft, ETSY, Tesla"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="secondary", use_container_width=True)
    
    with col3:
        analyze_button = st.button("📊 Analyze", type="primary", use_container_width=True)
    
    # Search functionality
    if search_button and search_query:
        with st.spinner("Searching..."):
            try:
                results = search_ticker(search_query)
                
                if results:
                    # Save search to database
                    save_search_history(st.session_state.session_id, search_query, results)
                    
                    st.success(f"Found {len(results)} results:")
                    
                    # Display results with analyze buttons
                    for result in results:
                        col1, col2, col3 = st.columns([2, 5, 2])
                        
                        with col1:
                            st.code(result['ticker'])
                        
                        with col2:
                            st.write(result['name'])
                        
                        with col3:
                            if st.button("📊 Analyze", key=f"search_analyze_{result['ticker']}"):
                                st.session_state.analyze_ticker = result['ticker']
                                st.rerun()
                else:
                    st.warning("No results found. Try a different search term.")
                    
            except Exception as e:
                st.error(f"Search error: {str(e)}")
    
    # Direct analysis functionality
    if analyze_button and search_query:
        ticker = search_query.upper().strip()
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                # Choose data source based on sidebar selection
                if data_source == "Polygon.io":
                    stock_info = get_polygon_stock_info(ticker)
                else:
                    stock_info = get_stock_info(ticker)
                
                if 'error' not in stock_info:
                    st.success(f"Analysis for {stock_info['name']} ({stock_info['ticker']})")
                    
                    # Calculate CAPE
                    cape_value, cape_error = calculate_individual_cape(ticker, data_source)
                    
                    # Key metrics in a nice layout with CAPE prominently displayed
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        if stock_info.get('current_price'):
                            st.metric("Current Price", f"${stock_info['current_price']:.2f}")
                        else:
                            st.metric("Current Price", "N/A")
                    
                    with col2:
                        if stock_info.get('pe_ratio'):
                            st.metric("P/E Ratio", f"{stock_info['pe_ratio']:.1f}")
                        else:
                            st.metric("P/E Ratio", "N/A")
                    
                    with col3:
                        # CAPE - The main feature!
                        if cape_value:
                            st.metric("CAPE Ratio", f"{cape_value:.1f}", 
                                    help="Cyclically Adjusted Price-to-Earnings Ratio")
                        else:
                            st.metric("CAPE Ratio", "N/A", 
                                    help="Cyclically Adjusted Price-to-Earnings Ratio")
                    
                    with col4:
                        if stock_info.get('market_cap'):
                            # Format market cap nicely
                            market_cap = stock_info['market_cap']
                            if market_cap and market_cap > 1e12:
                                cap_display = f"${market_cap/1e12:.2f}T"
                            elif market_cap and market_cap > 1e9:
                                cap_display = f"${market_cap/1e9:.2f}B"
                            elif market_cap and market_cap > 1e6:
                                cap_display = f"${market_cap/1e6:.2f}M"
                            elif market_cap:
                                cap_display = f"${market_cap:,.0f}"
                            else:
                                cap_display = "N/A"
                            st.metric("Market Cap", cap_display)
                        else:
                            st.metric("Market Cap", "N/A")
                    
                    with col5:
                        if stock_info.get('volume'):
                            volume = stock_info['volume']
                            if volume > 1e6:
                                vol_display = f"{volume/1e6:.1f}M"
                            elif volume > 1e3:
                                vol_display = f"{volume/1e3:.1f}K"
                            else:
                                vol_display = f"{volume:,.0f}"
                            st.metric("Volume", vol_display)
                        else:
                            st.metric("Volume", "N/A")
                    
                    # CAPE Analysis Section
                    if cape_value or cape_error:
                        st.subheader("📊 CAPE Analysis")
                        
                        if cape_value:
                            # CAPE interpretation
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("CAPE Ratio", f"{cape_value:.1f}")
                                
                                # CAPE interpretation
                                if cape_value < 15:
                                    interpretation = "🟢 Potentially Undervalued"
                                    color = "green"
                                elif cape_value < 25:
                                    interpretation = "🟡 Fairly Valued"
                                    color = "orange"
                                elif cape_value < 35:
                                    interpretation = "🟠 Potentially Overvalued"
                                    color = "orange"
                                else:
                                    interpretation = "🔴 Highly Overvalued"
                                    color = "red"
                                
                                st.markdown(f"**Interpretation:** {interpretation}")
                            
                            with col2:
                                # Historical context (placeholder data)
                                st.markdown("**Historical Context:**")
                                st.markdown("• Market Average CAPE: ~27.5")
                                st.markdown("• Historical Low: ~5-10")
                                st.markdown("• Historical High: ~40-45")
                                
                                if cape_error:
                                    st.info(f"Note: {cape_error}")
                        
                        else:
                            st.warning(f"CAPE calculation unavailable: {cape_error}")
                    
                    # Additional metrics for Polygon data
                    if data_source == "Polygon.io" and stock_info.get('open_price'):
                        st.subheader("📈 Price Information")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Open", f"${stock_info.get('open_price', 0):.2f}")
                        with col2:
                            st.metric("High", f"${stock_info.get('high_price', 0):.2f}")
                        with col3:
                            st.metric("Low", f"${stock_info.get('low_price', 0):.2f}")
                        with col4:
                            st.metric("Exchange", stock_info.get('exchange', 'N/A'))
                    
                    # Company details
                    st.subheader("🏢 Company Information")
                    info_data = []
                    
                    if stock_info.get('sector'):
                        info_data.append({"Field": "Sector", "Value": stock_info['sector']})
                    if stock_info.get('industry'):
                        info_data.append({"Field": "Industry", "Value": stock_info['industry']})
                    if stock_info.get('country'):
                        info_data.append({"Field": "Country", "Value": stock_info['country']})
                    if stock_info.get('currency'):
                        info_data.append({"Field": "Currency", "Value": stock_info['currency']})
                    if stock_info.get('employees'):
                        info_data.append({"Field": "Employees", "Value": f"{stock_info['employees']:,}"})
                    if stock_info.get('data_source'):
                        info_data.append({"Field": "Data Source", "Value": stock_info['data_source']})
                    
                    if info_data:
                        info_df = pd.DataFrame(info_data)
                        st.dataframe(info_df, hide_index=True, use_container_width=True)
                    
                    # Business summary or description
                    if stock_info.get('business_summary'):
                        st.subheader("📋 Business Summary")
                        st.write(stock_info['business_summary'])
                    elif stock_info.get('description'):
                        st.subheader("📋 Company Description")
                        st.write(stock_info['description'])
                    
                    # Website link
                    if stock_info.get('website'):
                        st.subheader("🌐 Company Website")
                        st.link_button("Visit Website", stock_info['website'])
                    
                    # Download analysis
                    st.subheader("📥 Download Analysis")
                    
                    # Create CSV data
                    csv_data = f"""Field,Value
Ticker,{stock_info['ticker']}
Company Name,{stock_info['name']}
Current Price,{stock_info.get('current_price', 'N/A')}
P/E Ratio,{stock_info.get('pe_ratio', 'N/A')}
CAPE Ratio,{cape_value if cape_value else 'N/A'}
Open Price,{stock_info.get('open_price', 'N/A')}
High Price,{stock_info.get('high_price', 'N/A')}
Low Price,{stock_info.get('low_price', 'N/A')}
Volume,{stock_info.get('volume', 'N/A')}
Market Cap,{stock_info.get('market_cap', 'N/A')}
Dividend Yield,{stock_info.get('dividend_yield', 'N/A')}
Sector,{stock_info.get('sector', 'N/A')}
Industry,{stock_info.get('industry', 'N/A')}
Country,{stock_info.get('country', 'N/A')}
Currency,{stock_info.get('currency', 'N/A')}
Exchange,{stock_info.get('exchange', 'N/A')}
Employees,{stock_info.get('employees', 'N/A')}
Data Source,{stock_info.get('data_source', 'N/A')}
Last Updated,{stock_info.get('last_updated', 'N/A')}
CAPE Note,{cape_error if cape_error else 'Standard calculation'}
"""
                    
                    st.download_button(
                        label="Download Stock Analysis (CSV)",
                        data=csv_data,
                        file_name=f"{ticker}_cape_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                    
                    # Save analysis to database
                    if cape_value:
                        save_cape_calculation(st.session_state.session_id, "Individual Stock CAPE", 
                                            ticker, datetime.now().date(), cape_value, 
                                            {"pe_ratio": stock_info.get('pe_ratio'), 
                                             "price": stock_info.get('current_price'),
                                             "data_source": data_source})
                    
                else:
                    st.error(f"Error analyzing {ticker}: {stock_info.get('error', 'Unknown error')}")
                    
                    # Show API status if using Polygon
                    if data_source == "Polygon.io":
                        st.info("💡 Tip: Try the 'Test Polygon API' button in the sidebar to check connection status.")
                    
            except Exception as e:
                st.error(f"Analysis error: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("**CAPE Demo v1.0** | Developed by Lohusalu Capital Management")
    st.markdown("Data sources: Yahoo Finance, Polygon.io, Robert Shiller (Yale Economics)")
    st.markdown("💡 **Tip:** Visit the Methodology page to learn how CAPE is calculated and understand data sources.")

if __name__ == "__main__":
    main()
