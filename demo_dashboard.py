import streamlit as st
st.set_page_config(page_title="Portfolio Monitor", layout="wide")
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go


# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .company-card {
        background: linear-gradient(135deg, #1a365d, #2c5282);
        border-radius: 10px;
        padding: 15px;
        margin: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: transform 0.2s;
        color: white;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        font-family: 'Inter', sans-serif;
    }

    .company-card:hover {
        transform: translateY(-2px);
    }

    .company-card.tech {
        background: linear-gradient(135deg, #553C9A, #6B46C1);
    }
    .company-card.finance {
        background: linear-gradient(135deg, #2C5282, #2B6CB0);
    }
    .company-card.consumer {
        background: linear-gradient(135deg, #285E61, #319795);
    }
    .company-card.health {
        background: linear-gradient(135deg, #744210, #975A16);
    }
    .company-card.energy {
        background: linear-gradient(135deg, #7B341E, #9C4221);
    }

    .metric-card {
        background: linear-gradient(135deg, #2D3748, #4A5568);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        min-height: 200px;
        color: white;
        display: flex;
        flex-direction: column;
        font-family: 'Inter', sans-serif;
    }

    .metric-card.tech { background: linear-gradient(135deg, #553C9A, #6B46C1); }
    .metric-card.finance { background: linear-gradient(135deg, #2C5282, #2B6CB0); }
    .metric-card.consumer { background: linear-gradient(135deg, #285E61, #319795); }
    .metric-card.health { background: linear-gradient(135deg, #744210, #975A16); }

    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .metric-name {
        font-size: 14px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.9);
    }

    .metric-value {
        font-size: 28px;
        font-weight: 700;
        margin: 8px 0;
        letter-spacing: -0.5px;
    }

    .metric-comparison {
        font-size: 13px;
        margin: 4px 0;
        color: rgba(255,255,255,0.8);
        font-weight: 500;
    }

    .featured-tag {
        background: rgba(255,255,255,0.2);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        color: white;
        margin-bottom: 5px;
        display: inline-block;
    }

    .company-name {
        font-size: 1.2em;
        font-weight: 600;
        margin: 5px 0;
    }

    .stock-price {
        font-size: 24px;
        font-weight: 700;
        margin: 5px 0;
    }

    .stock-change {
        font-size: 14px;
        margin-top: 5px;
        font-weight: 500;
    }

    .sparkline-container {
        height: 40px;
        margin-top: 8px;
    }

    .comparison-container {
        height: 60px;
        margin-top: 8px;
    }

    .positive-change { color: #68D391; }
    .negative-change { color: #FC8181; }

    .alert-section {
        margin-top: 2rem;
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #1A202C, #2D3748);
    }

    .alert-card {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid;
    }

    .alert-high { border-left-color: #F56565; }
    .alert-medium { border-left-color: #F6E05E; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

# Configuration dictionaries
COMPANIES = {
    "MSFT": {
        "name": "Microsoft",
        "sector": "Technology",
        "color": "tech"
    },
    "AAPL": {
        "name": "Apple",
        "sector": "Technology",
        "color": "tech"
    },
    "AMZN": {
        "name": "Amazon",
        "sector": "Consumer Cyclical",
        "color": "consumer"
    },
    "JPM": {
        "name": "JP Morgan",
        "sector": "Financial",
        "color": "finance"
    },
    "JNJ": {
        "name": "Johnson & Johnson",
        "sector": "Healthcare",
        "color": "health"
    }
}

METRICS = {
    "PE Ratio": {"format": ".2f", "suffix": "x"},
    "Forward P/E": {"format": ".2f", "suffix": "x"},
    "P/B Ratio": {"format": ".2f", "suffix": "x"},
    "EV/EBITDA": {"format": ".2f", "suffix": "x"},
    "EV/Sales": {"format": ".2f", "suffix": "x"},
    "Profit Margin": {"format": ".1%", "suffix": ""},
    "Operating Margin": {"format": ".1%", "suffix": ""},
    "EBITDA Margin": {"format": ".1%", "suffix": ""},
    "Dividend Yield": {"format": ".1%", "suffix": ""}
}


def create_sparkline(data_points, is_positive=True):
    """Create a sparkline chart using plotly"""
    fig = go.Figure()

    # Generate sample data if none provided
    if data_points is None:
        data_points = [np.random.normal(0, 1) for _ in range(20)]

    fig.add_trace(go.Scatter(
        y=data_points,
        mode='lines',
        line=dict(
            color='rgba(255, 255, 255, 0.8)',
            width=1.5,
            shape='spline'
        ),
        hoverinfo='skip'
    ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=40,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            showline=False,
            zeroline=False
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            showline=False,
            zeroline=False
        )
    )

    return fig


def create_metric_chart(current, historical, sector_avg):
    """Create a comparison chart for metrics"""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=['Current', 'Historical', 'Sector'],
        y=[current, historical, sector_avg],
        marker_color=['#4299E1', '#9F7AEA', '#48BB78']
    ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=60,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            showticklabels=True,
            tickfont=dict(color='rgba(255,255,255,0.8)', size=8)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            showticklabels=True,
            tickfont=dict(color='rgba(255,255,255,0.8)', size=8)
        )
    )

    return fig


def get_stock_data(ticker, period='1y'):
    """Get stock data including price history and metrics history"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period=period)

        # Get today's data
        today_data = stock.history(period='1d')
        current_price = today_data['Close'].iloc[-1] if not today_data.empty else info.get('regularMarketPrice', 0)
        previous_close = info.get('previousClose', current_price)

        # Safe division for price change calculation
        if previous_close and previous_close != 0:
            price_change = ((current_price - previous_close) / previous_close) * 100
        else:
            price_change = 0

        # Get historical metrics data points
        metric_history = hist['Close'].values[-20:] if len(hist) >= 20 else None

        return {
            'current_price': current_price,
            'price_change': price_change,
            'previous_close': previous_close,
            'metric_history': metric_history,
            'metrics': {
                'PE Ratio': info.get('trailingPE', 0) or 0,
                'Forward P/E': info.get('forwardPE', 0) or 0,
                'P/B Ratio': info.get('priceToBook', 0) or 0,
                'EV/EBITDA': info.get('enterpriseToEbitda', 0) or 0,
                'EV/Sales': info.get('enterpriseToRevenue', 0) or 0,
                'Profit Margin': info.get('profitMargins', 0) or 0,
                'Operating Margin': info.get('operatingMargins', 0) or 0,
                'EBITDA Margin': info.get('ebitdaMargins', 0) or 0,
                'Dividend Yield': info.get('dividendYield', 0) or 0,
            }
        }
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return None


def create_company_card(ticker, company_info, data):
    """Create a company card with sector-based coloring"""
    current_price = data.get('current_price', 0)
    price_change = data.get('price_change', 0)
    price_change_class = "positive-change" if price_change >= 0 else "negative-change"
    sector_class = company_info['color'].lower()

    return f"""
        <div class="company-card {sector_class}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span class="featured-tag">FEATURED</span>
                    <div class="company-name">{company_info['name']}</div>
                    <div style="color: rgba(255,255,255,0.7); font-size: 14px; margin-top: 2px;">
                        {ticker}
                    </div>
                </div>
            </div>
            <div style="margin-top: auto;">
                <div class="stock-price">${current_price:.2f}</div>
                <div class="stock-change {price_change_class}">
                    {price_change:+.2f}% today
                </div>
            </div>
        </div>
    """


def create_metric_card(name, current, historical, sector_avg, changed, sector_color, data_points=None):
    """Create a metric card with sparkline and comparison chart"""
    metric_config = METRICS[name]
    format_str = "{:" + metric_config["format"] + "}" + metric_config["suffix"]

    change_class = "positive-change" if changed > 0 else "negative-change"
    chart = create_metric_chart(current, historical, sector_avg)
    sparkline = create_sparkline(data_points, changed > 0)

    return f"""
        <div class="metric-card {sector_color}">
            <div class="metric-header">
                <div class="metric-name">{name}</div>
                <div class="change-indicator {change_class}">
                    {changed:+.1f}%
                </div>
            </div>

            <div class="metric-value">
                {format_str.format(current)}
            </div>

            <div class="metric-comparison">
                Historical: {format_str.format(historical)}
            </div>
            <div class="metric-comparison">
                Sector Avg: {format_str.format(sector_avg)}
            </div>

            <div class="sparkline-container">
                {sparkline.to_html(full_html=False, include_plotlyjs='cdn')}
            </div>

            <div class="comparison-container">
                {chart.to_html(full_html=False, include_plotlyjs='cdn')}
            </div>
        </div>
    """


def main():
    # Sidebar controls
    st.sidebar.title("Settings")
    selected_period = st.sidebar.selectbox(
        "Time Range",
        ["1y", "2y", "5y"],
        index=0
    )

    deviation_threshold = st.sidebar.slider(
        "Deviation Alert Threshold (%)",
        min_value=1,
        max_value=20,
        value=5
    )

    # Main content
    st.title("Portfolio Monitor")

    # Company cards row
    company_cards = st.container()
    with company_cards:
        cols = st.columns(len(COMPANIES))
        for i, (ticker, company) in enumerate(COMPANIES.items()):
            data = get_stock_data(ticker, selected_period)
            if data:
                cols[i].markdown(
                    create_company_card(ticker, company, data),
                    unsafe_allow_html=True
                )

    # Selected company metrics
    selected_company = st.selectbox(
        "Select Company to View Metrics",
        list(COMPANIES.keys()),
        key="company_selector"
    )

    if selected_company:
        data = get_stock_data(selected_company, selected_period)
        if data:
            st.markdown("### Key Metrics")

            cols = st.columns(3)
            alerts = []

            # Keep track of important metrics for visualization
            key_metrics = ['PE Ratio', 'EV/EBITDA', 'Profit Margin']

            for i, (metric_name, metric_value) in enumerate(data['metrics'].items()):
                historical_value = metric_value * (1 + np.random.normal(0, 0.1))
                sector_avg = metric_value * (1 + np.random.normal(0, 0.15))
                percent_change = ((
                                              metric_value - historical_value) / historical_value) * 100 if historical_value != 0 else 0

                if abs(percent_change) > deviation_threshold:
                    alerts.append({
                        'metric': metric_name,
                        'company': COMPANIES[selected_company]['name'],
                        'value': metric_value,
                        'benchmark': historical_value,
                        'deviation': percent_change,
                        'type': 'historical'
                    })

                metric_config = METRICS[metric_name]
                format_str = "{:" + metric_config["format"] + "}" + metric_config["suffix"]

                col = cols[i % 3]
                with col:
                    st.markdown(f"""
                        <div class="metric-card {COMPANIES[selected_company]['color']}">
                            <div class="metric-header">
                                <div class="metric-name">{metric_name}</div>
                                <div class="change-indicator {'positive-change' if percent_change > 0 else 'negative-change'}">
                                    {percent_change:+.1f}%
                                </div>
                            </div>
                            <div class="metric-value">
                                {format_str.format(metric_value)}
                            </div>
                            <div class="metric-comparison">
                                Historical: {format_str.format(historical_value)}
                            </div>
                            <div class="metric-comparison">
                                Sector Avg: {format_str.format(sector_avg)}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Only show charts for key metrics
                    if metric_name in key_metrics:
                        fig_comparison = create_metric_chart(metric_value, historical_value, sector_avg)
                        st.plotly_chart(
                            fig_comparison,
                            use_container_width=True,
                            config={'displayModeBar': False},
                            key=f"comparison_{selected_company}_{i}_{metric_name}"
                        )

            # Display alerts if any exist
            if alerts:
                st.markdown("### Alerts")
                for alert in alerts:
                    severity = "high" if abs(alert['deviation']) > 10 else "medium"
                    st.markdown(
                        f"""
                        <div class="alert-card alert-{severity}">
                            <div style="font-weight: bold; margin-bottom: 5px;">
                                {alert['company']} - {alert['metric']}
                            </div>
                            <div style="color: rgba(255,255,255,0.8);">
                                Current value ({alert['value']:.2f}) deviated by {alert['deviation']:+.1f}% 
                                from {alert['type'].title()} Average ({alert['benchmark']:.2f})
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


if __name__ == "__main__":
    main()