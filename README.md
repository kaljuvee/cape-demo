# CAPE Demo - Cyclically Adjusted PE Analysis

A Streamlit application for analyzing CAPE (Cyclically Adjusted Price-to-Earnings) ratios for S&P 500 stocks, developed by [Julian Kaljuvee](https://kaljuvee.github.io).

## Features

- **Equal-Weight CAPE Calculation**: Calculate CAPE ratios using equal-weighting methodology
- **Cap-Weight vs Equal-Weight Comparison**: Compare different CAPE calculation approaches
- **Ticker Search**: Search and analyze individual stocks
- **Data Downloads**: Export analysis results
- **Session Storage**: SQLite database for storing session data
- **Interactive Visualizations**: Plotly charts for data visualization

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run Home.py
```

## Data Sources

- **Shiller Data**: Robert Shiller's monthly real-EPS series from Yale Economics
- **Stock Data**: Yahoo Finance via yfinance library
- **S&P 500 Constituents**: Wikipedia list of current S&P 500 companies

## Methodology

The application implements the equal-weight CAPE calculation as described in academic literature:

1. Downloads historical S&P 500 constituent data
2. Calculates 10-year real earnings per share for each stock
3. Computes individual stock CAPE ratios
4. Equal-weights the ratios across all constituents
5. Compares results to traditional cap-weighted CAPE

## Caveats

- yfinance earnings data is trailing twelve months and not CPI-adjusted
- Survivorship bias: uses current S&P 500 names for historical analysis
- Rebalancing frequency may differ from official equal-weight index methodology

## License

MIT License
