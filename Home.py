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

# Import utility functions
from utils.yfinance_utils import (
    get_shiller_data, 
    get_sp500_tickers, 
    calculate_cape_comparison,
    search_ticker,
    get_stock_info
)
from utils.db_utils import (
    init_database,
    create_session,
    update_session_access,
    save_cape_calculation,
    get_cape_calculations,
    save_search_history,
    get_search_history,
    get_session_stats
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

# Session management
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    create_session(st.session_state.session_id)

update_session_access(st.session_state.session_id)

# Main header
st.title("📈 CAPE Demo")
st.subheader("Cyclically Adjusted PE Analysis")
st.markdown("*Developed by Lohusalu Capital Management*")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    
    # Session stats
    stats = get_session_stats(st.session_state.session_id)
    if stats:
        st.metric("Calculations", stats.get('calculations_count', 0))
        st.metric("Searches", stats.get('searches_count', 0))
    
    st.markdown("---")
    
    # Quick actions
    st.header("Quick Actions")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("📊 Calculate CAPE"):
        st.session_state.show_cape_calc = True

# Main content area - Merged tabs
tab1, tab2, tab3 = st.tabs(["📊 CAPE Analysis", "🔍 Stock Analysis", "📋 Session History"])

with tab1:
    st.header("CAPE Analysis")
    
    # Methodology explanation
    with st.expander("📖 Methodology & Caveats"):
        st.markdown("""
        ### Equal-Weight CAPE Calculation
        
        This application calculates CAPE (Cyclically Adjusted Price-to-Earnings) ratios using both traditional cap-weighted 
        and equal-weighted methodologies.
        
        **Process:**
        1. Download S&P 500 constituent data from Wikipedia
        2. Fetch historical price and earnings data via yfinance
        3. Calculate 10-year real earnings per share for each stock
        4. Compute individual stock CAPE ratios
        5. Equal-weight the ratios across all constituents
        6. Compare to traditional cap-weighted CAPE from Shiller data
        
        ### Important Caveats
        
        - **Data Limitations**: yfinance earnings data is trailing twelve months and not CPI-adjusted; 
          for full rigor you would download company 10-K EPS and CPI-deflate yourself.
        
        - **Survivorship Bias**: The analysis uses today's 500 names for the entire history. 
          To be perfect you need the historical membership (S&P provides this commercially, 
          or you can scrape it from Siblis Research).
        
        - **Rebalancing Frequency**: The equal-weight index is rebalanced quarterly; this analysis uses monthly data. 
          Switch to quarterly if you want to match the S&P 500 Equal Weight Index methodology exactly.
        """)
    
    # CAPE calculation section
    if st.button("Calculate CAPE Comparison", type="primary"):
        with st.spinner("Calculating CAPE ratios... This may take a few minutes."):
            try:
                comparison_data = calculate_cape_comparison()
                
                if comparison_data is not None and not comparison_data.empty:
                    st.success("CAPE calculation completed!")
                    
                    # Store in session state
                    st.session_state.cape_data = comparison_data
                    
                    # Save to database
                    for date, row in comparison_data.iterrows():
                        if not pd.isna(row.get('Equal_Weight_CAPE')):
                            save_cape_calculation(
                                st.session_state.session_id,
                                'equal_weight',
                                'SPY',
                                date.strftime('%Y-%m-%d'),
                                row['Equal_Weight_CAPE']
                            )
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(
                            "Latest Cap-Weight CAPE", 
                            f"{comparison_data['Cap_Weight_CAPE_Shiller'].iloc[-1]:.1f}"
                        )
                    
                    with col2:
                        if 'Equal_Weight_CAPE' in comparison_data.columns:
                            st.metric(
                                "Latest Equal-Weight CAPE", 
                                f"{comparison_data['Equal_Weight_CAPE'].iloc[-1]:.1f}"
                            )
                    
                    # Plot comparison
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=comparison_data.index,
                        y=comparison_data['Cap_Weight_CAPE_Shiller'],
                        mode='lines',
                        name='Cap-Weight CAPE (Shiller)',
                        line=dict(color='blue')
                    ))
                    
                    if 'Equal_Weight_CAPE' in comparison_data.columns:
                        fig.add_trace(go.Scatter(
                            x=comparison_data.index,
                            y=comparison_data['Equal_Weight_CAPE'],
                            mode='lines',
                            name='Equal-Weight CAPE',
                            line=dict(color='red')
                        ))
                    
                    fig.update_layout(
                        title="S&P 500 CAPE: Cap-Weight vs Equal-Weight",
                        xaxis_title="Date",
                        yaxis_title="CAPE Ratio",
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Download section
                    st.subheader("📥 Download Data")
                    
                    # Convert to CSV
                    csv_buffer = io.StringIO()
                    comparison_data.to_csv(csv_buffer)
                    csv_data = csv_buffer.getvalue()
                    
                    st.download_button(
                        label="Download CAPE Data (CSV)",
                        data=csv_data,
                        file_name=f"cape_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                    
                else:
                    st.error("Failed to calculate CAPE data. Please try again.")
                    
            except Exception as e:
                st.error(f"Error calculating CAPE: {str(e)}")
    
    # Display cached data if available
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
                    stock_info = get_stock_info(ticker)
                    
                    if 'error' not in stock_info:
                        st.success(f"Analysis for {stock_info['name']} ({stock_info['ticker']})")
                        
                        # Key metrics in a nice layout
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            if stock_info['current_price']:
                                st.metric("Current Price", f"${stock_info['current_price']:.2f}")
                            else:
                                st.metric("Current Price", "N/A")
                        
                        with col2:
                            if stock_info['pe_ratio']:
                                st.metric("P/E Ratio", f"{stock_info['pe_ratio']:.1f}")
                            else:
                                st.metric("P/E Ratio", "N/A")
                        
                        with col3:
                            if stock_info['market_cap']:
                                # Format market cap nicely
                                market_cap = stock_info['market_cap']
                                if market_cap > 1e12:
                                    cap_display = f"${market_cap/1e12:.2f}T"
                                elif market_cap > 1e9:
                                    cap_display = f"${market_cap/1e9:.2f}B"
                                elif market_cap > 1e6:
                                    cap_display = f"${market_cap/1e6:.2f}M"
                                else:
                                    cap_display = f"${market_cap:,.0f}"
                                st.metric("Market Cap", cap_display)
                            else:
                                st.metric("Market Cap", "N/A")
                        
                        with col4:
                            if stock_info['dividend_yield']:
                                st.metric("Dividend Yield", f"{stock_info['dividend_yield']:.2%}")
                            else:
                                st.metric("Dividend Yield", "N/A")
                        
                        # Company details
                        st.subheader("Company Information")
                        info_data = []
                        
                        if stock_info.get('sector'):
                            info_data.append({"Field": "Sector", "Value": stock_info['sector']})
                        if stock_info.get('industry'):
                            info_data.append({"Field": "Industry", "Value": stock_info['industry']})
                        if stock_info.get('country'):
                            info_data.append({"Field": "Country", "Value": stock_info['country']})
                        if stock_info.get('employees'):
                            info_data.append({"Field": "Employees", "Value": f"{stock_info['employees']:,}"})
                        
                        if info_data:
                            info_df = pd.DataFrame(info_data)
                            st.dataframe(info_df, hide_index=True, use_container_width=True)
                        
                        # Business summary
                        if stock_info.get('business_summary'):
                            st.subheader("Business Summary")
                            st.write(stock_info['business_summary'])
                        
                        # Download analysis
                        st.subheader("📥 Download Analysis")
                        
                        # Create CSV data
                        csv_data = f"""Field,Value
Ticker,{stock_info['ticker']}
Company Name,{stock_info['name']}
Current Price,{stock_info.get('current_price', 'N/A')}
P/E Ratio,{stock_info.get('pe_ratio', 'N/A')}
Market Cap,{stock_info.get('market_cap', 'N/A')}
Dividend Yield,{stock_info.get('dividend_yield', 'N/A')}
Sector,{stock_info.get('sector', 'N/A')}
Industry,{stock_info.get('industry', 'N/A')}
Country,{stock_info.get('country', 'N/A')}
Employees,{stock_info.get('employees', 'N/A')}
"""
                        
                        st.download_button(
                            label="Download Stock Analysis (CSV)",
                            data=csv_data,
                            file_name=f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                        
                    else:
                        st.error(f"Error analyzing {ticker}: {stock_info.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"Analysis error: {str(e)}")
    
    # Recent searches
    st.markdown("---")
    st.subheader("🕒 Recent Searches")
    recent_searches = get_search_history(st.session_state.session_id, limit=5)
    
    if not recent_searches.empty:
        for _, search in recent_searches.iterrows():
            with st.expander(f"'{search['search_query']}' - {search['created_at']}"):
                results = search['results']
                if results:
                    for result in results:
                        col1, col2, col3 = st.columns([2, 5, 2])
                        
                        with col1:
                            st.code(result['ticker'])
                        
                        with col2:
                            st.write(result['name'])
                        
                        with col3:
                            if st.button("📊 Analyze", key=f"recent_{result['ticker']}_{search['created_at']}"):
                                st.session_state.analyze_ticker = result['ticker']
                                st.rerun()
                else:
                    st.write("No results found")
    else:
        st.info("No recent searches.")

with tab3:
    st.header("📋 Session History")
    
    # Session statistics
    stats = get_session_stats(st.session_state.session_id)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Calculations", stats.get('calculations_count', 0))
    with col2:
        st.metric("Total Searches", stats.get('searches_count', 0))
    with col3:
        st.metric("Session ID", st.session_state.session_id[:8] + "...")
    
    # CAPE calculations history
    st.subheader("🧮 CAPE Calculations")
    cape_history = get_cape_calculations(st.session_state.session_id)
    
    if not cape_history.empty:
        st.dataframe(cape_history, use_container_width=True)
        
        # Download calculations
        csv_buffer = io.StringIO()
        cape_history.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="Download Calculations (CSV)",
            data=csv_data,
            file_name=f"cape_calculations_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No CAPE calculations in this session yet.")
    
    # Search history
    st.subheader("🔍 Search History")
    search_history = get_search_history(st.session_state.session_id)
    
    if not search_history.empty:
        for _, search in search_history.iterrows():
            with st.expander(f"'{search['search_query']}' - {search['created_at']}"):
                results = search['results']
                if results:
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df, hide_index=True, use_container_width=True)
                else:
                    st.write("No results")
    else:
        st.info("No search history in this session yet.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>CAPE Demo v1.0 | Developed by Lohusalu Capital Management</p>
    <p>Data sources: Yahoo Finance, Robert Shiller (Yale Economics), Wikipedia</p>
</div>
""", unsafe_allow_html=True)
