import streamlit as st
import pandas as pd
import numpy as np
from intrinio_sdk.rest import ApiException
import intrinio_sdk
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Configure Intrinio API
intrinio_sdk.ApiClient().configuration.api_key['api_key'] = st.secrets["INTRINIO_API_KEY"]
security_api = intrinio_sdk.SecurityApi()
company_api = intrinio_sdk.CompanyApi()

# Sample portfolio data structure
PORTFOLIO = [
    ("Technology", "Software", "MSFT"),
    ("Technology", "Hardware", "AAPL"),
    ("Healthcare", "Biotechnology", "AMGN"),
    # Add more stocks as needed
]


class MetricsTracker:
    def __init__(self):
        self.metrics_list = [
            'pe_ratio', 'ev_to_ebitda', 'price_to_book_value', 'ev_to_sales',
            'gross_margin', 'operating_margin', 'ebitda_margin', 'net_margin',
            'revenue_growth_yoy', 'revenue_growth_qoq', 'dividend_yield',
            'forward_pe_ratio', 'forward_ev_to_ebitda', 'current_ratio',
            'quick_ratio', 'interest_coverage'
        ]

    def get_historical_data(self, ticker, metric, lookback_years=5):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_years * 365)

            data = security_api.get_security_historical_data(
                ticker,
                metric,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                frequency='quarterly'
            )

            return pd.DataFrame([{
                'date': point.date,
                'value': point.value
            } for point in data.historical_data])

        except ApiException as e:
            st.error(f"Error fetching {metric} data for {ticker}: {e}")
            return pd.DataFrame()

    def calculate_deviations(self, historical_data, current_value):
        if historical_data.empty:
            return None

        periods = {
            'Last Quarter': 1,
            'Last Year': 4,
            '3 Years': 12,
            '5 Years': 20
        }

        deviations = {}
        for period_name, num_quarters in periods.items():
            if len(historical_data) >= num_quarters:
                period_data = historical_data.tail(num_quarters)
                mean = period_data['value'].mean()
                std = period_data['value'].std()
                deviation = (current_value - mean) / std if std != 0 else 0
                deviations[period_name] = deviation

        return deviations

    def get_current_metrics(self, ticker):
        try:
            metrics = {}
            for metric in self.metrics_list:
                data = security_api.get_security_historical_data(
                    ticker,
                    metric,
                    start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    end_date=datetime.now().strftime('%Y-%m-%d')
                )
                if data.historical_data:
                    metrics[metric] = data.historical_data[-1].value
            return metrics
        except ApiException as e:
            st.error(f"Error fetching current metrics for {ticker}: {e}")
            return {}


def main():
    st.title("Portfolio Metrics Monitor")

    tracker = MetricsTracker()

    # Sidebar for filtering
    st.sidebar.header("Filters")
    selected_sectors = st.sidebar.multiselect(
        "Select Sectors",
        options=list(set(stock[0] for stock in PORTFOLIO))
    )

    # Main content
    col1, col2 = st.columns(2)

    with col1:
        st.header("Portfolio Overview")

        # Filter portfolio based on selected sectors
        filtered_portfolio = PORTFOLIO if not selected_sectors else [
            stock for stock in PORTFOLIO if stock[0] in selected_sectors
        ]

        # Create portfolio summary
        portfolio_df = pd.DataFrame(filtered_portfolio, columns=['Sector', 'Industry', 'Ticker'])
        st.dataframe(portfolio_df)

    with col2:
        st.header("Metrics Alerts")
        alert_container = st.empty()

    # Metrics Analysis
    st.header("Detailed Metrics Analysis")

    for sector, industry, ticker in filtered_portfolio:
        with st.expander(f"{ticker} - {industry} ({sector})"):
            current_metrics = tracker.get_current_metrics(ticker)

            if current_metrics:
                metrics_df = pd.DataFrame([current_metrics]).T
                metrics_df.columns = ['Current Value']

                # Calculate historical deviations
                deviations = {}
                for metric in tracker.metrics_list:
                    if metric in current_metrics:
                        historical_data = tracker.get_historical_data(ticker, metric)
                        metric_deviations = tracker.calculate_deviations(
                            historical_data,
                            current_metrics[metric]
                        )
                        if metric_deviations:
                            deviations[metric] = metric_deviations

                # Display metrics and deviations
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Current Metrics")
                    st.dataframe(metrics_df)

                with col2:
                    st.subheader("Significant Deviations (>5σ)")
                    for metric, devs in deviations.items():
                        for period, deviation in devs.items():
                            if abs(deviation) > 5:
                                st.warning(
                                    f"{metric}: {deviation:.2f}σ deviation from "
                                    f"{period} average"
                                )

                # Historical trends visualization
                st.subheader("Historical Trends")
                metric_to_plot = st.selectbox(
                    "Select metric to visualize",
                    options=tracker.metrics_list,
                    key=f"metric_select_{ticker}"
                )

                historical_data = tracker.get_historical_data(ticker, metric_to_plot)
                if not historical_data.empty:
                    fig = px.line(
                        historical_data,
                        x='date',
                        y='value',
                        title=f"{metric_to_plot} Historical Trend"
                    )
                    st.plotly_chart(fig)


if __name__ == "__main__":
    st.set_page_config(
        page_title="Portfolio Metrics Monitor",
        page_icon="📊",
        layout="wide"
    )
    main()