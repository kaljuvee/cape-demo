"""
CAPE Demo - Cyclically Adjusted PE Analysis
Main Streamlit Application
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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    page_title="CAPE Demo - Lohusalu Capital Management",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_database()

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

def main():
    # Header
    st.markdown("# 📈 CAPE Demo")
    st.markdown("### Cyclically Adjusted PE Analysis")
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
            ["Yahoo Finance (yfinance)", "Polygon.io"],
            index=1,  # Default to Polygon
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
        
        if st.button("📊 Calculate CAPE"):
            st.session_state.show_cape = True
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📊 CAPE Analysis", "🔍 Stock Analysis", "📋 Session History"])
    
    with tab1:
        st.header("📊 CAPE Analysis")
        
        # Methodology section
        with st.expander("📖 Methodology & Caveats"):
            st.markdown("""
            ### Equal-Weight CAPE Calculation
            
            This application calculates CAPE (Cyclically Adjusted Price-to-Earnings) ratios using both traditional cap-weighted and equal-weighted methodologies.
            
            **Process:**
            1. Download S&P 500 constituent data from Wikipedia
            2. Fetch historical price and earnings data via yfinance
            3. Calculate 10-year real earnings per share for each stock
            4. Compute individual stock CAPE ratios
            5. Equal-weight the ratios across all constituents
            6. Compare to traditional cap-weighted CAPE from Shiller data
            
            ### Important Caveats
            
            - **Data Limitations**: yfinance earnings data is trailing twelve months and not CPI-adjusted; for full rigor you would download company 10-K EPS and CPI-deflate yourself.
            
            - **Survivorship Bias**: The analysis uses today's 500 names for the entire history. To be perfect you need the historical membership (S&P provides this commercially, or you can scrape it from Siblis Research).
            
            - **Rebalancing Frequency**: The equal-weight index is rebalanced quarterly; this analysis uses monthly data. Switch to quarterly if you want to match the S&P 500 Equal Weight Index methodology exactly.
            """)
        
        # CAPE calculation button
        if st.button("Calculate CAPE Comparison"):
            with st.spinner("Calculating CAPE ratios... This may take several minutes."):
                try:
                    cape_data = calculate_cape_comparison()
                    
                    if cape_data is not None and not cape_data.empty:
                        # Save calculation to database
                        save_cape_calculation(st.session_state.session_id, "CAPE Comparison", "SPX", datetime.now().date(), cape_data['cape_ew'].iloc[-1], cape_data.to_dict())
                        
                        st.success("CAPE calculation completed!")
                        
                        # Display results
                        st.subheader("📊 CAPE Comparison Results")
                        
                        # Create visualization
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=cape_data.index,
                            y=cape_data['cape_cw'],
                            mode='lines',
                            name='Cap-Weighted CAPE',
                            line=dict(color='blue', width=2)
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=cape_data.index,
                            y=cape_data['cape_ew'],
                            mode='lines',
                            name='Equal-Weighted CAPE',
                            line=dict(color='red', width=2)
                        ))
                        
                        fig.update_layout(
                            title="CAPE Ratio Comparison: Cap-Weighted vs Equal-Weighted",
                            xaxis_title="Date",
                            yaxis_title="CAPE Ratio",
                            hovermode='x unified',
                            template='plotly_white'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Summary statistics
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Cap-Weighted CAPE")
                            st.metric("Current", f"{cape_data['cape_cw'].iloc[-1]:.1f}")
                            st.metric("Average", f"{cape_data['cape_cw'].mean():.1f}")
                            st.metric("Std Dev", f"{cape_data['cape_cw'].std():.1f}")
                        
                        with col2:
                            st.subheader("Equal-Weighted CAPE")
                            st.metric("Current", f"{cape_data['cape_ew'].iloc[-1]:.1f}")
                            st.metric("Average", f"{cape_data['cape_ew'].mean():.1f}")
                            st.metric("Std Dev", f"{cape_data['cape_ew'].std():.1f}")
                        
                        # Download option
                        csv_data = cape_data.to_csv()
                        st.download_button(
                            label="Download CAPE Data (CSV)",
                            data=csv_data,
                            file_name=f"cape_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                        
                        # Store in session state for later use
                        st.session_state.cape_data = cape_data
                        
                    else:
                        st.error("Failed to calculate CAPE data. Please check the data sources and try again.")
                        
                except Exception as e:
                    st.error(f"Error calculating CAPE: {str(e)}")
        
        # Display cached CAPE data if available
        if 'cape_data' in st.session_state:
            st.subheader("📊 Current CAPE Data")
            st.dataframe(st.session_state.cape_data.tail(10), use_container_width=True)

    with tab2:
        st.header("🔍 Stock Analysis")
        
        # Unified Ticker Search section
        st.subheader("🔍 Ticker Search")
        
        # Check if ticker was selected from search
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
                        
                        # Key metrics in a nice layout
                        col1, col2, col3, col4 = st.columns(4)
                        
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
                        
                        with col4:
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
                        st.subheader("Company Information")
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
                            st.subheader("Business Summary")
                            st.write(stock_info['business_summary'])
                        elif stock_info.get('description'):
                            st.subheader("Company Description")
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
Open Price,{stock_info.get('open_price', 'N/A')}
High Price,{stock_info.get('high_price', 'N/A')}
Low Price,{stock_info.get('low_price', 'N/A')}
Volume,{stock_info.get('volume', 'N/A')}
P/E Ratio,{stock_info.get('pe_ratio', 'N/A')}
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
"""
                        
                        st.download_button(
                            label="Download Stock Analysis (CSV)",
                            data=csv_data,
                            file_name=f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                        
                    else:
                        st.error(f"Error analyzing {ticker}: {stock_info.get('error', 'Unknown error')}")
                        
                        # Show API status if using Polygon
                        if data_source == "Polygon.io":
                            st.info("💡 Tip: Try the 'Test Polygon API' button in the sidebar to check connection status.")
                        
                except Exception as e:
                    st.error(f"Analysis error: {str(e)}")
    
    # Recent searches
    st.markdown("---")
    
    with tab3:
        st.header("📋 Session History")
        
        # Search history
        st.subheader("🔍 Recent Searches")
        try:
            search_history = get_search_history(st.session_state.session_id)
            
            if not search_history.empty:
                # Display search history
                for _, row in search_history.iterrows():
                    with st.expander(f"'{row['search_query']}' - {row['created_at']}"):
                        results = row['results']
                        if isinstance(results, list):
                            for result in results:
                                col1, col2, col3 = st.columns([2, 5, 2])
                                with col1:
                                    st.code(result.get('ticker', 'N/A'))
                                with col2:
                                    st.write(result.get('name', 'N/A'))
                                with col3:
                                    if st.button("📊 Analyze", key=f"history_analyze_{result.get('ticker', 'unknown')}_{row.name}"):
                                        st.session_state.analyze_ticker = result.get('ticker', '')
                                        st.rerun()
                
                # Download search history
                csv_data = search_history.to_csv(index=False)
                st.download_button(
                    label="Download Search History (CSV)",
                    data=csv_data,
                    file_name=f"search_history_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No recent searches.")
                
        except Exception as e:
            st.error(f"Error loading search history: {str(e)}")
        
        # Calculation history
        st.subheader("📊 Recent Calculations")
        try:
            calc_history = get_cape_calculations(st.session_state.session_id)
            
            if not calc_history.empty:
                st.dataframe(calc_history, use_container_width=True)
                
                # Download calculation history
                csv_data = calc_history.to_csv(index=False)
                st.download_button(
                    label="Download Calculation History (CSV)",
                    data=csv_data,
                    file_name=f"calculation_history_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No recent calculations.")
                
        except Exception as e:
            st.error(f"Error loading calculation history: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("**CAPE Demo v1.0** | Developed by Lohusalu Capital Management")
    st.markdown("Data sources: Yahoo Finance, Polygon.io, Robert Shiller (Yale Economics), Wikipedia")

if __name__ == "__main__":
    main()
