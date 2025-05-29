import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import sqlite3

import os 
from dotenv import load_dotenv 
load_dotenv()

# API key for FRED 
API_KEY_FRED = os.environ.get('API_KEY_FRED')
tickers = {'CPIAUCSL': 'CPI', #all cpi related are SA 
           'CPILFESL': 'Core CPI', 
           'CPIUFDSL': 'CPI Food', 
           'CPIENGSL': 'CPI Energy', 
           'PCEPI': 'PCE', 
           'PCEPILFE': 'Core PCE',
           'CUSR0000SACL1E': 'CPI Core Goods',
           'CUSR0000SASLE': 'CPI Core Service',
           'CUSR0000SAH1': 'Shelter',
           'CUSR0000SAM2': 'Medical Care', 
           'CUSR0000SAS4': 'Transportation',
           'CPIEDUSL':'Education and Communication', 
           'CPIRECSL':'Recreation'
           } 

########### funtion #############
def fetchFred(api_key, tickers):
  combine = pd.DataFrame()
  updates = pd.Series(dtype='float')

  for i in tickers.keys(): 
      url = f'https://api.stlouisfed.org/fred/series?series_id={i}{api_key}' # get latest release date
      df = pd.read_xml(url, parse_dates=['last_updated'])
      updates[tickers[i]] = (df['last_updated'][0])

      url = f'https://api.stlouisfed.org/fred/series/observations?series_id={i}{api_key}' # get data
      df = pd.read_xml(url, parse_dates=['date'])
      df.set_index('date', inplace=True)
      filt = (df['value'] != '.') # some data from fred is in weird . string
      single = df[filt]['value'].apply(lambda x: float(x)).to_frame(tickers[i]) # excluding . and turn into float
      combine = pd.concat([combine, single], axis=1)

  combine.index.name = 'date_column'
  combine = combine.sort_index()
  return updates, combine

########### Scrape and save into DB #############
cpi_update, cpi_df = fetchFred(API_KEY_FRED, tickers)

cpi_update = pd.DataFrame(cpi_update)
cpi_update.columns=['Latest update']

cpi_df.index.name = 'date_column' # Name your index column

# Connect to your SQLite database
conn = sqlite3.connect('headlines.db') # Assuming you're adding to your existing DB

# Store the DataFrame
# index=True will store the DataFrame's index (your datetime index) as a column
# if_exists='replace' will overwrite the table if it exists, 'append' would add rows
cpi_df.to_sql('fred_cpi_data', conn, if_exists='replace', index=True)
cpi_update.to_sql('fred_cpi_update_time', conn, if_exists='replace', index=True)

conn.close()