"""
Individual Stock Analysis Page
Developed by Lohusalu Capital Management
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import io

from utils.yfinance_utils import get_stock_info
from utils.db_utils import save_cape_calculation, update_session_access

st.set_page_config(
    page_title="Stock Analysis - CAPE Demo",
    page_icon="📈",
    layout="wide"
)

# Update session access
if 'session_id' in st.session_state:
    update_session_access(st.session_state.session_id)

st.title("📈 Individual Stock Analysis")
st.markdown("*Detailed analysis of individual stocks*")

# Navigation
if st.button("← Back to Home"):
    st.switch_page("Home.py")

# Get ticker from session state or input
ticker = None
if 'selected_ticker' in st.session_state:
    ticker = st.session_state.selected_ticker
    company_name = st.session_state.get('selected_name', ticker)
    st.info(f"Analyzing: {company_name} ({ticker})")
else:
    ticker = st.text_input("Enter ticker symbol:", placeholder="e.g., AAPL").upper()

if ticker:
    try:
        # Get stock object
        stock = yf.Ticker(ticker)
        
        # Tabs for different analyses
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Price History", "💰 Financials", "📋 Details"])
        
        with tab1:
            st.header(f"Overview - {ticker}")
            
            # Get basic info
            with st.spinner("Loading stock information..."):
                stock_info = get_stock_info(ticker)
                
                if 'error' not in stock_info:
                    # Key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if stock_info['current_price']:
                            st.metric("Current Price", f"${stock_info['current_price']:.2f}")
                    
                    with col2:
                        if stock_info['pe_ratio']:
                            st.metric("P/E Ratio", f"{stock_info['pe_ratio']:.1f}")
                    
                    with col3:
                        if stock_info['market_cap']:
                            market_cap_b = stock_info['market_cap'] / 1e9
                            st.metric("Market Cap", f"${market_cap_b:.1f}B")
                    
                    with col4:
                        if stock_info['dividend_yield']:
                            st.metric("Dividend Yield", f"{stock_info['dividend_yield']:.2%}")
                    
                    # Company information
                    st.subheader("Company Information")
                    
                    info_data = [
                        {"Field": "Company Name", "Value": stock_info.get('name', 'N/A')},
                        {"Field": "Sector", "Value": stock_info.get('sector', 'N/A')},
                        {"Field": "Industry", "Value": stock_info.get('industry', 'N/A')},
                    ]
                    
                    info_df = pd.DataFrame(info_data)
                    st.dataframe(info_df, hide_index=True, use_container_width=True)
                    
                else:
                    st.error(f"Error loading data for {ticker}: {stock_info.get('error', 'Unknown error')}")
        
        with tab2:
            st.header(f"Price History - {ticker}")
            
            # Time period selection
            period_options = {
                "1 Month": "1mo",
                "3 Months": "3mo", 
                "6 Months": "6mo",
                "1 Year": "1y",
                "2 Years": "2y",
                "5 Years": "5y"
            }
            
            selected_period = st.selectbox("Select time period:", list(period_options.keys()), index=3)
            
            with st.spinner("Loading price data..."):
                try:
                    # Get historical data
                    hist_data = stock.history(period=period_options[selected_period])
                    
                    if not hist_data.empty:
                        # Price chart
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=hist_data.index,
                            y=hist_data['Close'],
                            mode='lines',
                            name='Close Price',
                            line=dict(color='blue')
                        ))
                        
                        fig.update_layout(
                            title=f"{ticker} Price History ({selected_period})",
                            xaxis_title="Date",
                            yaxis_title="Price ($)",
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Volume chart
                        fig_vol = go.Figure()
                        
                        fig_vol.add_trace(go.Bar(
                            x=hist_data.index,
                            y=hist_data['Volume'],
                            name='Volume',
                            marker_color='lightblue'
                        ))
                        
                        fig_vol.update_layout(
                            title=f"{ticker} Volume ({selected_period})",
                            xaxis_title="Date",
                            yaxis_title="Volume",
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig_vol, use_container_width=True)
                        
                        # Price statistics
                        st.subheader("Price Statistics")
                        
                        price_stats = {
                            "Current Price": f"${hist_data['Close'].iloc[-1]:.2f}",
                            "Period High": f"${hist_data['High'].max():.2f}",
                            "Period Low": f"${hist_data['Low'].min():.2f}",
                            "Average Volume": f"{hist_data['Volume'].mean():,.0f}",
                            "Price Change": f"{((hist_data['Close'].iloc[-1] / hist_data['Close'].iloc[0]) - 1) * 100:.1f}%"
                        }
                        
                        stats_df = pd.DataFrame(list(price_stats.items()), columns=["Metric", "Value"])
                        st.dataframe(stats_df, hide_index=True, use_container_width=True)
                        
                        # Download data
                        st.subheader("📥 Download Data")
                        
                        csv_buffer = io.StringIO()
                        hist_data.to_csv(csv_buffer)
                        csv_data = csv_buffer.getvalue()
                        
                        st.download_button(
                            label=f"Download {ticker} Price Data (CSV)",
                            data=csv_data,
                            file_name=f"{ticker}_price_data_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                        
                    else:
                        st.warning(f"No price data available for {ticker}")
                        
                except Exception as e:
                    st.error(f"Error loading price data: {str(e)}")
        
        with tab3:
            st.header(f"Financial Data - {ticker}")
            
            with st.spinner("Loading financial data..."):
                try:
                    # Get financial data
                    info = stock.info
                    
                    # Key financial metrics
                    st.subheader("Key Financial Metrics")
                    
                    financial_metrics = {}
                    
                    # Revenue and profitability
                    if 'totalRevenue' in info:
                        financial_metrics['Total Revenue'] = f"${info['totalRevenue']:,.0f}"
                    if 'grossMargins' in info:
                        financial_metrics['Gross Margin'] = f"{info['grossMargins']:.2%}"
                    if 'operatingMargins' in info:
                        financial_metrics['Operating Margin'] = f"{info['operatingMargins']:.2%}"
                    if 'profitMargins' in info:
                        financial_metrics['Profit Margin'] = f"{info['profitMargins']:.2%}"
                    
                    # Valuation metrics
                    if 'trailingPE' in info:
                        financial_metrics['P/E Ratio (TTM)'] = f"{info['trailingPE']:.1f}"
                    if 'forwardPE' in info:
                        financial_metrics['Forward P/E'] = f"{info['forwardPE']:.1f}"
                    if 'priceToBook' in info:
                        financial_metrics['Price-to-Book'] = f"{info['priceToBook']:.1f}"
                    if 'enterpriseToRevenue' in info:
                        financial_metrics['EV/Revenue'] = f"{info['enterpriseToRevenue']:.1f}"
                    
                    # Financial strength
                    if 'totalCash' in info:
                        financial_metrics['Total Cash'] = f"${info['totalCash']:,.0f}"
                    if 'totalDebt' in info:
                        financial_metrics['Total Debt'] = f"${info['totalDebt']:,.0f}"
                    if 'returnOnEquity' in info:
                        financial_metrics['Return on Equity'] = f"{info['returnOnEquity']:.2%}"
                    if 'returnOnAssets' in info:
                        financial_metrics['Return on Assets'] = f"{info['returnOnAssets']:.2%}"
                    
                    if financial_metrics:
                        metrics_df = pd.DataFrame(list(financial_metrics.items()), columns=["Metric", "Value"])
                        st.dataframe(metrics_df, hide_index=True, use_container_width=True)
                    else:
                        st.warning("Limited financial data available")
                    
                    # Quarterly earnings (if available)
                    try:
                        quarterly_earnings = stock.quarterly_earnings
                        if not quarterly_earnings.empty:
                            st.subheader("Quarterly Earnings")
                            st.dataframe(quarterly_earnings.head(8), use_container_width=True)
                    except:
                        st.info("Quarterly earnings data not available")
                    
                except Exception as e:
                    st.error(f"Error loading financial data: {str(e)}")
        
        with tab4:
            st.header(f"Detailed Information - {ticker}")
            
            with st.spinner("Loading detailed information..."):
                try:
                    info = stock.info
                    
                    # Business summary
                    if 'longBusinessSummary' in info:
                        st.subheader("Business Summary")
                        st.write(info['longBusinessSummary'])
                    
                    # Key executives (if available)
                    if 'companyOfficers' in info and info['companyOfficers']:
                        st.subheader("Key Executives")
                        officers_data = []
                        for officer in info['companyOfficers'][:5]:  # Top 5
                            officers_data.append({
                                'Name': officer.get('name', 'N/A'),
                                'Title': officer.get('title', 'N/A'),
                                'Age': officer.get('age', 'N/A')
                            })
                        
                        if officers_data:
                            officers_df = pd.DataFrame(officers_data)
                            st.dataframe(officers_df, hide_index=True, use_container_width=True)
                    
                    # Additional company info
                    st.subheader("Company Details")
                    
                    company_details = {}
                    
                    if 'website' in info:
                        company_details['Website'] = info['website']
                    if 'fullTimeEmployees' in info:
                        company_details['Full-time Employees'] = f"{info['fullTimeEmployees']:,}"
                    if 'city' in info and 'state' in info:
                        company_details['Headquarters'] = f"{info['city']}, {info['state']}"
                    if 'country' in info:
                        company_details['Country'] = info['country']
                    if 'phone' in info:
                        company_details['Phone'] = info['phone']
                    
                    if company_details:
                        details_df = pd.DataFrame(list(company_details.items()), columns=["Field", "Value"])
                        st.dataframe(details_df, hide_index=True, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error loading detailed information: {str(e)}")
    
    except Exception as e:
        st.error(f"Error analyzing {ticker}: {str(e)}")

else:
    st.info("Please enter a ticker symbol to begin analysis.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Individual Stock Analysis | Developed by Lohusalu Capital Management</p>
</div>
""", unsafe_allow_html=True)
