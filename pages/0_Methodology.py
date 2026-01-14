"""\nCAPE Methodology and Data Sources\nExplains how CAPE is calculated and data sources used\nDeveloped by [Julian Kaljuvee](https://kaljuvee.github.io)\n"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="CAPE Methodology - Julian Kaljuvee",
    page_icon="📚",
    layout="wide"
)

def main():
    # Header
    st.markdown("# 📚 CAPE Methodology & Data Sources")
    st.markdown("### Understanding Cyclically Adjusted Price-to-Earnings Ratios")
    st.markdown("*Developed by [Julian Kaljuvee](https://kaljuvee.github.io)*")
    
    # Introduction
    st.markdown("---")
    st.header("🎯 What is CAPE?")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **CAPE (Cyclically Adjusted Price-to-Earnings)** is a valuation measure that uses real earnings 
        per share over a 10-year period to smooth out fluctuations in corporate profits that occur 
        over different periods of a business cycle.
        
        **Key Features:**
        - Uses **10-year average** of inflation-adjusted earnings
        - Smooths out business cycle fluctuations
        - Provides long-term valuation perspective
        - Originally developed by **Robert Shiller** (Nobel Prize winner)
        - Also known as **PE10** or **Shiller PE**
        """)
    
    with col2:
        # Simple CAPE formula visualization
        st.markdown("""
        ### 📊 CAPE Formula
        
        ```
        CAPE = Current Price / 
               Average(Real Earnings, 10 years)
        ```
        
        **Where:**
        - Current Price = Today's stock price
        - Real Earnings = Inflation-adjusted earnings
        - 10 years = Rolling 10-year period
        """)
    
    # Methodology Section
    st.markdown("---")
    st.header("🔬 Calculation Methodology")
    
    # Create tabs for different aspects
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Individual Stocks", "📊 Market Indices", "⚠️ Limitations", "🔍 Data Sources"])
    
    with tab1:
        st.subheader("Individual Stock CAPE Calculation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Step-by-Step Process:
            
            1. **Collect Historical Data**
               - 10+ years of annual earnings per share
               - Consumer Price Index (CPI) data for inflation adjustment
               - Current stock price
            
            2. **Adjust for Inflation**
               - Convert all historical earnings to today's dollars
               - Use CPI to calculate real (inflation-adjusted) earnings
            
            3. **Calculate 10-Year Average**
               - Take the mean of 10 years of real earnings
               - This smooths out business cycle effects
            
            4. **Compute CAPE**
               - Divide current price by 10-year average real earnings
               - Result is the CAPE ratio
            """)
        
        with col2:
            # Create a sample CAPE calculation visualization
            years = list(range(2014, 2024))
            nominal_earnings = [2.5, 2.8, 3.1, 3.4, 3.8, 4.2, 3.9, 4.5, 5.1, 5.8]
            cpi_adjustment = [0.85, 0.87, 0.89, 0.91, 0.93, 0.95, 0.97, 0.99, 1.01, 1.00]
            real_earnings = [nom * cpi for nom, cpi in zip(nominal_earnings, cpi_adjustment)]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=years, y=nominal_earnings, 
                mode='lines+markers', name='Nominal Earnings',
                line=dict(color='blue', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=years, y=real_earnings, 
                mode='lines+markers', name='Real Earnings (CPI-adjusted)',
                line=dict(color='red', width=2)
            ))
            
            avg_real = np.mean(real_earnings)
            fig.add_hline(y=avg_real, line_dash="dash", line_color="green",
                         annotation_text=f"10-Year Average: ${avg_real:.2f}")
            
            fig.update_layout(
                title="Sample Earnings History (Hypothetical)",
                xaxis_title="Year",
                yaxis_title="Earnings per Share ($)",
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show calculation
            current_price = 150
            cape_value = current_price / avg_real
            st.metric("Sample CAPE Calculation", f"{cape_value:.1f}", 
                     f"${current_price} ÷ ${avg_real:.2f}")
    
    with tab2:
        st.subheader("📊 How to Read the CAPE vs P/E Signal")
        
        st.markdown("""
        ### Understanding CAPE vs P/E Comparison
        
        The relationship between CAPE and P/E ratios provides crucial insights into earnings cycles and future returns:
        """)
        
        # Signal interpretation boxes
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background-color: #ffebee; padding: 20px; border-radius: 10px; border-left: 5px solid #f44336;">
            <h4>🔴 CAPE > P/E Signal</h4>
            <p><strong>Current profits above trend</strong></p>
            <ul>
            <li><strong>Expectation:</strong> Mean-reversion in earnings; the "E" in P/E is likely to fall</li>
            <li><strong>Risk:</strong> Unless the price falls in tandem, the stock is more expensive than the headline P/E suggests</li>
            <li><strong>Historical Pattern:</strong> This regime is followed by <strong>below-average forward 5-10 year returns</strong></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; border-left: 5px solid #4caf50;">
            <h4>🟢 CAPE < P/E Signal</h4>
            <p><strong>Current profits below trend</strong></p>
            <ul>
            <li><strong>Expectation:</strong> Recovery in earnings; the "E" in P/E is likely to rise</li>
            <li><strong>Opportunity:</strong> The stock may be cheaper than the scary P/E implies</li>
            <li><strong>Historical Pattern:</strong> This regime is followed by <strong>above-average forward 5-10 year returns</strong></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 📈 Investment Implications
        
        **Key Insight:** CAPE helps identify whether current earnings are temporarily high or low relative to the long-term trend.
        
        - **When CAPE > P/E:** Current earnings may be unsustainably high (earnings peak)
        - **When CAPE < P/E:** Current earnings may be temporarily depressed (earnings trough)
        
        This framework helps investors avoid the trap of extrapolating current earnings indefinitely into the future.
        """)
        
        st.subheader("Market Index CAPE (S&P 500)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Equal-Weight vs Cap-Weight CAPE:
            
            **Cap-Weighted CAPE (Traditional):**
            - Uses market capitalization weights
            - Larger companies have more influence
            - Follows Robert Shiller's original methodology
            - Available from Yale Economics website
            
            **Equal-Weight CAPE (Alternative):**
            - Each stock gets equal weight regardless of size
            - Reduces impact of mega-cap stocks
            - May provide different market perspective
            - Calculated using individual stock CAPEs
            """)
        
        with col2:
            st.markdown("""
            ### Our Implementation:
            
            1. **Download S&P 500 constituents** from Wikipedia
            2. **Fetch historical data** via yfinance API
            3. **Calculate individual CAPEs** for each stock
            4. **Aggregate using different weighting schemes:**
               - Equal-weight: Simple average of all CAPEs
               - Cap-weight: Weighted by market capitalization
            5. **Compare results** to Shiller's official data
            
            ### Data Sources:
            - **Stock prices**: Yahoo Finance / Polygon.io
            - **Earnings data**: Company financial statements
            - **CPI data**: Federal Reserve Economic Data
            - **S&P 500 list**: Wikipedia (current constituents)
            """)
    
    with tab3:
        st.subheader("⚠️ Important Limitations & Caveats")
        
        st.warning("""
        **Please be aware of these important limitations in our implementation:**
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Data Limitations:
            
            **🔴 Earnings Data Quality:**
            - yfinance provides trailing twelve months (TTM) earnings
            - **Not CPI-adjusted** for inflation
            - May not match official company 10-K filings
            - **Recommendation**: Use official SEC filings for precision
            
            **🔴 Survivorship Bias:**
            - Uses today's S&P 500 constituents for entire history
            - Doesn't account for companies that were removed
            - **Impact**: May overestimate historical performance
            - **Solution**: Use historical membership data (available commercially)
            """)
        
        with col2:
            st.markdown("""
            ### Methodological Limitations:
            
            **🔴 Rebalancing Frequency:**
            - Equal-weight index rebalanced quarterly in reality
            - Our analysis uses monthly data
            - **Impact**: May not match official equal-weight indices exactly
            
            **🔴 Individual Stock CAPE:**
            - Simplified calculation for demonstration
            - May use estimated values when data unavailable
            - **Note**: Full implementation requires extensive historical data
            
            **🔴 Real-Time Data:**
            - API rate limits may affect data freshness
            - Some calculations use approximations
            """)
        
        st.info("""
        **💡 For Production Use:** Consider upgrading to premium data sources, 
        implementing proper CPI adjustments, and using historical S&P 500 membership data.
        """)
    
    with tab4:
        st.subheader("🔍 Data Sources & APIs")
        
        # Data sources table
        data_sources = [
            {
                "Source": "Robert Shiller (Yale Economics)",
                "Data Type": "Historical S&P 500 CAPE",
                "URL": "http://www.econ.yale.edu/~shiller/data/ie_data.xls",
                "Usage": "Benchmark cap-weighted CAPE data",
                "Quality": "🟢 Authoritative"
            },
            {
                "Source": "Yahoo Finance (yfinance)",
                "Data Type": "Stock prices, earnings, company info",
                "URL": "https://finance.yahoo.com/",
                "Usage": "Individual stock analysis",
                "Quality": "🟡 Good (rate limited)"
            },
            {
                "Source": "Polygon.io",
                "Data Type": "Real-time stock data, company details",
                "URL": "https://polygon.io/",
                "Usage": "Primary stock data source",
                "Quality": "🟢 Professional grade"
            },
            {
                "Source": "Wikipedia",
                "Data Type": "S&P 500 constituent list",
                "URL": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                "Usage": "Current S&P 500 members",
                "Quality": "🟡 Current only"
            },
            {
                "Source": "Federal Reserve (FRED)",
                "Data Type": "Consumer Price Index (CPI)",
                "URL": "https://fred.stlouisfed.org/",
                "Usage": "Inflation adjustment (future)",
                "Quality": "🟢 Official government data"
            }
        ]
        
        df_sources = pd.DataFrame(data_sources)
        st.dataframe(df_sources, use_container_width=True, hide_index=True)
        
        # API Information
        st.markdown("---")
        st.subheader("🔧 API Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Polygon.io Setup:
            
            **Default Configuration:**
            - Built-in API key for immediate testing
            - Professional-grade rate limits
            - Real-time and historical data access
            
            **Custom Setup:**
            1. Get your API key from [polygon.io](https://polygon.io/)
            2. Add to Streamlit secrets or environment variables:
               ```
               POLYGON_API_KEY = "your_api_key_here"
               ```
            3. Restart the application
            """)
        
        with col2:
            st.markdown("""
            ### Yahoo Finance (yfinance):
            
            **Limitations:**
            - Free tier with strict rate limits
            - May experience 429 errors under heavy use
            - No API key required
            
            **Best Practices:**
            - Use for occasional queries only
            - Implement caching for repeated requests
            - Consider Polygon.io for production use
            """)
    
    # Historical Context
    st.markdown("---")
    st.header("📊 Historical CAPE Context")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### S&P 500 CAPE Historical Ranges:
        
        **Typical Values:**
        - **Historical Average**: ~17-20
        - **Fair Value Range**: 15-25
        - **Overvalued Territory**: 25-35
        - **Extreme Overvaluation**: 35+
        
        **Historical Extremes:**
        - **Lowest (1920s Depression)**: ~5-7
        - **Highest (Dot-com Bubble, 2000)**: ~44
        - **Recent High (2021)**: ~38
        - **Current (2024)**: ~30-35
        """)
    
    with col2:
        # Create a sample historical CAPE chart
        years = list(range(1990, 2025))
        # Simplified historical CAPE approximation
        cape_values = [
            15, 16, 17, 18, 20, 22, 25, 28, 32, 35,  # 1990s
            44, 40, 35, 30, 25, 20, 18, 16, 15, 14,  # 2000s
            16, 18, 20, 22, 24, 26, 28, 30, 32, 35,  # 2010s
            38, 35, 32, 30, 28                       # 2020s
        ]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years, y=cape_values,
            mode='lines', name='S&P 500 CAPE',
            line=dict(color='blue', width=3)
        ))
        
        # Add reference lines
        fig.add_hline(y=17, line_dash="dash", line_color="green",
                     annotation_text="Historical Average (~17)")
        fig.add_hline(y=25, line_dash="dash", line_color="orange",
                     annotation_text="Overvalued Threshold (25)")
        fig.add_hline(y=35, line_dash="dash", line_color="red",
                     annotation_text="Extreme Overvaluation (35)")
        
        fig.update_layout(
            title="S&P 500 CAPE History (Approximation)",
            xaxis_title="Year",
            yaxis_title="CAPE Ratio",
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Implementation Notes
    st.markdown("---")
    st.header("💻 Implementation Notes")
    
    with st.expander("🔧 Technical Implementation Details"):
        st.markdown("""
        ### Code Structure:
        
        **Main Application (`Home.py`):**
        - Stock search and analysis interface
        - Individual stock CAPE calculations
        - Real-time data integration
        
        **Utility Modules:**
        - `utils/yfinance_utils.py`: Yahoo Finance integration
        - `utils/polygon_utils.py`: Polygon.io API wrapper
        - `utils/db_utils.py`: SQLite database operations
        
        **Key Functions:**
        ```python
        def calculate_individual_cape(ticker, data_source):
            # Simplified CAPE calculation for individual stocks
            # In production: fetch 10 years of earnings data
            # Adjust for inflation using CPI
            # Return CAPE ratio
        
        def calculate_cape_comparison():
            # Compare cap-weighted vs equal-weighted CAPE
            # Uses Shiller data for cap-weighted
            # Calculates equal-weighted from individual stocks
        ```
        
        ### Database Schema:
        - **Sessions**: Track user sessions and statistics
        - **Search History**: Store ticker searches and results
        - **CAPE Calculations**: Cache calculated CAPE values
        - **Data Cache**: Store API responses to reduce calls
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("**CAPE Demo v1.0** | Developed by [Julian Kaljuvee](https://kaljuvee.github.io)")
    st.markdown("📚 **References:** Shiller, R. J. (2000). *Irrational Exuberance*. Princeton University Press.")
    st.markdown("🔗 **Official Shiller Data:** [Yale Economics](http://www.econ.yale.edu/~shiller/data.htm)")

if __name__ == "__main__":
    main()
