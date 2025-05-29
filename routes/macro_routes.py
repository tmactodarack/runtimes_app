import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for
import pandas as pd

import plotly.graph_objects as go
import plotly.io as pio

# 1. Create a Blueprint object
# The first argument, 'blog', is the name of the blueprint.
# The second argument, __name__, is the import name of the blueprint's package.
macro_bp = Blueprint('macro', __name__)

DB_FILE = 'headlines.db'

# 2. Define routes using the Blueprint decorator
@macro_bp.route('/')
def cpi_fetch():
    conn = sqlite3.connect(DB_FILE)

    df = pd.read_sql_query('''
                        SELECT * 
                        FROM fred_cpi_data
                                                    
                        ''',
                            conn,
                            index_col='date_column',
                            parse_dates=['date_column']
                            )

    update_df = pd.read_sql_query('''SELECT * 
                            FROM fred_cpi_update_time
                            ''',
                            conn,
                            index_col='index'
                            )
    
    active = df[['CPI', 'Core CPI']].pct_change(12,fill_method=None).iloc[-12:]
    update = pd.to_datetime(update_df.loc['CPI'].iloc[0])
    title = 'CPI YoY vs Core CPI YoY'

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=active.index, y=active['CPI'], name='CPI YoY', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=active.index, y=active['Core CPI'], name='Core CPI YoY', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=[active.index[-1]], y=[fig.data[0]['y'][-1]-0.002], mode='markers', marker_symbol='triangle-up', marker_color='red', name='Latest Release: ' + f"{update:%m/%d/%y}" + f" ({active.index[-1]:%b})"))
    # fig.add_vline(x=data.index[-1], line_width=3, line_dash="dash", line_color="green")
    fig.update_layout(template='seaborn', 
                    showlegend=True,
                    title=dict(text=title, font=dict(size=25)),
                    margin=dict(b=0,t=80,r=0,l=0),
                    legend = dict(orientation='h',x=1, y=-0.15, xanchor='right', yanchor='top'), 
                    # legend = dict(x=0.01, y=0.99, xanchor='left', yanchor='top'),
                    xaxis=dict(fixedrange=True), 
                    yaxis=dict(tickformat='.1%', fixedrange=True))
    
    fig_html = pio.to_html(fig, full_html=False)

    return render_template ('macro.html', fig_html=fig_html)
