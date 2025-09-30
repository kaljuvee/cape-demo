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

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["📊 CAPE Analysis", "🔍 Ticker Search", "📈 Individual Stock", "📋 Session History"])

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
    st.header("🔍 Ticker Search")
    
    # Search interface
    search_query = st.text_input("Search for stocks (ticker or company name):", placeholder="e.g., AAPL, Apple, Microsoft")
    
    if st.button("Search") and search_query:
        with st.spinner("Searching..."):
            try:
                results = search_ticker(search_query)
                
                if results:
                    # Save search to database
                    save_search_history(st.session_state.session_id, search_query, results)
                    
                    st.success(f"Found {len(results)} results:")
                    
                    # Display results
                    for result in results:
                        col1, col2, col3 = st.columns([2, 4, 2])
                        
                        with col1:
                            st.code(result['ticker'])
                        
                        with col2:
                            st.write(result['name'])
                        
                        with col3:
                            if st.button(f"Analyze", key=f"analyze_{result['ticker']}"):
                                st.session_state.selected_ticker = result['ticker']
                                st.session_state.selected_name = result['name']
                                st.switch_page("pages/stock_analysis.py")
                else:
                    st.warning("No results found. Try a different search term.")
                    
            except Exception as e:
                st.error(f"Search error: {str(e)}")
    
    # Recent searches
    st.subheader("🕒 Recent Searches")
    recent_searches = get_search_history(st.session_state.session_id, limit=5)
    
    if not recent_searches.empty:
        for _, search in recent_searches.iterrows():
            with st.expander(f"'{search['search_query']}' - {search['created_at']}"):
                results = search['results']
                for result in results:
                    st.write(f"• {result['ticker']}: {result['name']}")
    else:
        st.info("No recent searches.")

with tab3:
    st.header("📈 Individual Stock Analysis")
    
    # Ticker input
    ticker_input = st.text_input("Enter ticker symbol:", placeholder="e.g., AAPL").upper()
    
    if st.button("Analyze Stock") and ticker_input:
        with st.spinner(f"Analyzing {ticker_input}..."):
            try:
                stock_info = get_stock_info(ticker_input)
                
                if 'error' not in stock_info:
                    st.success(f"Analysis for {stock_info['name']} ({stock_info['ticker']})")
                    
                    # Display stock information
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if stock_info['current_price']:
                            st.metric("Current Price", f"${stock_info['current_price']:.2f}")
                    
                    with col2:
                        if stock_info['pe_ratio']:
                            st.metric("P/E Ratio", f"{stock_info['pe_ratio']:.1f}")
                    
                    with col3:
                        if stock_info['market_cap']:
                            st.metric("Market Cap", f"${stock_info['market_cap']:,.0f}")
                    
                    with col4:
                        if stock_info['dividend_yield']:
                            st.metric("Dividend Yield", f"{stock_info['dividend_yield']:.2%}")
                    
                    # Company details
                    st.subheader("Company Information")
                    info_df = pd.DataFrame([
                        {"Field": "Sector", "Value": stock_info.get('sector', 'N/A')},
                        {"Field": "Industry", "Value": stock_info.get('industry', 'N/A')},
                    ])
                    st.dataframe(info_df, hide_index=True, use_container_width=True)
                    
                else:
                    st.error(f"Error analyzing {ticker_input}: {stock_info.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Analysis error: {str(e)}")

with tab4:
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
