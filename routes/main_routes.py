import os
from dotenv import load_dotenv 
load_dotenv()

from flask import Blueprint, render_template, request, jsonify
import plotly.graph_objs as go
import plotly.io as pio
import requests
import pandas as pd
from io import StringIO
import sqlite3
import json
from plotly.utils import PlotlyJSONEncoder
from openai import OpenAI

# --- Configuration ---
API_KEY_TWELVEDATA = os.environ.get('API_KEY_TWELVEDATA')
API_KEY_CHATGPT = os.environ.get('API_KEY_CHATGPT')
DB_FILE = 'headlines.db'
client = OpenAI(api_key=API_KEY_CHATGPT)

# --- Blueprint Definition ---
main_bp = Blueprint('main', __name__)

# --- Helper Functions (Moved from app.py) ---
def get_price_data(ticker):
    # ... (code for get_price_data helper function)
    url = 'https://api.twelvedata.com/time_series'
    params = {'symbol': ticker, 'interval': '1day', 'outputsize': 365, 'apikey': API_KEY_TWELVEDATA}
    response = requests.get(url, params=params)
    data = response.json()
    if data.get('status') != 'ok': return None, None
    df = pd.DataFrame(data['values'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    df = df.astype(float)
    fig = go.Figure(go.Scatter(x=df.index, y=df['close'], mode='lines'))
    fig_html = pio.to_html(fig, full_html=False)
    price_data_frame = df[['close']].head(5).to_html(classes='table table-striped')
    return fig_html, price_data_frame

def get_key_stats(ticker):
    # ... (code for get_key_stats helper function)
    url = f'https://finance.yahoo.com/quote/{ticker}/key-statistics'
    response = requests.get(url, headers={'User-agent':'Mozilla/5.0 Firefox'}).text
    tables = pd.read_html(StringIO(response))
    stats_df = tables[0]
    stats_df.set_index(stats_df.iloc[:,0], inplace=True)
    stats_df.index.name = None
    stats_df = stats_df.iloc[[0, 2, 3], 1]
    stats_df.name = ticker
    return pd.DataFrame(stats_df).to_html(classes='table table-striped')

def get_news_summary(conn, table_name, summary_table_name):
    # ... (code for get_news_summary helper function)
    
    conn.row_factory = sqlite3.Row # To access by column name
    c = conn.cursor()
    # Get the latest summary directly from SQLite
    c.execute(f"SELECT * FROM {summary_table_name} ORDER BY timestamp DESC LIMIT 1")
    summary_row = c.fetchone()
    
    latest_headlines_df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT 5", conn)

    return summary_row['news'], latest_headlines_df.to_html(index=False, classes='table table-sm')


# --- Main Routes using the Blueprint ---
@main_bp.route('/')
def index():
    ticker = request.args.get("ticker", "NVDA").upper()
    conn = sqlite3.connect(DB_FILE)
    fig_html, price_data_frame = get_price_data(ticker)
    key_stats_html = get_key_stats(ticker)
    reuters_summary, reuters_html = get_news_summary(conn, 'reuters_headlines', 'reuters_headlines_summary')
    cnbc_summary, cnbc_html = get_news_summary(conn, 'CNBC_headlines', 'CNBC_headlines_summary')
    conn.close()
    return render_template('index.html', ticker=ticker, fig_html=fig_html, price_data_frame=price_data_frame, PE=key_stats_html, reuters=reuters_html, all_reuters_news_summary=reuters_summary, cnbc=cnbc_html, all_cnbc_news_summary=cnbc_summary)


@main_bp.route('/get_stock')
def get_stock():
    ticker = request.args.get("ticker", "NVDA").upper()

    # === Fetch price data ===
    url = 'https://api.twelvedata.com/time_series'
    params = {
        'symbol': ticker,
        'interval': '1day',
        'outputsize': 365,
        'apikey': API_KEY_TWELVEDATA,
        'format': 'JSON'
    }
    response = requests.get(url, params=params)
    data = response.json()

    try:
        df = pd.DataFrame(data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        df = df.astype(float)

        # Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines+markers'))
        
        fig.update_layout(
            title=f'{ticker} Stock Price',
            xaxis_rangeslider_visible=False,
            xaxis=dict(
                type="date",
                tickformatstops=[
                    dict(dtickrange=[None, 1000], value="%H:%M:%S.%L ms"),
                    dict(dtickrange=[1000, 60000], value="%H:%M:%S"),
                    dict(dtickrange=[60000, 3600000], value="%H:%M"),
                    dict(dtickrange=[3600000, 86400000], value="%H:%M<br>%Y-%m-%d"),
                    dict(dtickrange=[86400000, 604800000], value="%b %d<br>%Y"),
                    dict(dtickrange=[604800000, "M1"], value="%b %d"),
                    dict(dtickrange=["M1", "M12"], value="%b %Y"),
                    dict(dtickrange=["M12", None], value="%Y")
                ]
            ),
            yaxis_title="Close Price"
        ) 

        chart_data_json_str = json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)
        chart_data = json.loads(chart_data_json_str)

        # chart_data = fig.to_dict()
        # fig_html = pio.to_html(fig, full_html=False)

        # Table
        price_table = df[['close']].head(5).to_html(classes='table table-striped')

        return jsonify({
            'ticker': ticker,
            'price_table': price_table,
            'chart_data': {
                    'data': chart_data['data'],
                    'layout': chart_data['layout']
            }
        })

    except Exception as e:
        # If an error occurs (e.g., invalid ticker), return an error message
        # and an empty chart.
        return jsonify({
            'ticker': ticker,
            'price_table': f"<p class='text-danger'>Error fetching data for {ticker}. Please check the ticker and try again.</p>",
            'chart_data': {
                    'data': [],
                    'layout': {'title': f'No data available for {ticker}'}
            }
        })