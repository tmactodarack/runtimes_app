import os 
from dotenv import load_dotenv 
load_dotenv()

import pandas as pd
from playwright.sync_api import sync_playwright
import sqlite3
import datetime
from openai import OpenAI

API_KEY_CHATGPT = os.environ.get('API_KEY_CHATGPT')
DB_FILE = 'headlines.db'
client = OpenAI(api_key=API_KEY_CHATGPT)

####################### Prepare db #######################    
conn = sqlite3.connect('headlines.db')
c = conn.cursor()

####################### Function #######################    
def get_news_summary(conn, table_name):
    # ... (code for get_news_summary helper function)
    query = f"SELECT * FROM {table_name} WHERE DATE(timestamp) = DATE('now', 'localtime')"
    news_df = pd.read_sql_query(query, conn)
    if news_df.empty: return    f"No {table_name.split('_')[0].upper()} news found for today.", pd.DataFrame().to_html()
    prompt = f"Parse these headlines, tell me the time range, and summarize in four sentences using Traditional Chinese: {news_df.to_string()}"
    response = client.chat.completions.create(model="gpt-4.1-nano", messages=[{"role": "user", "content": prompt}])
    summary = response.choices[0].message.content
    return summary

####################### Scraping Reuters Headlines #######################    
url = 'http://www.reuters.com'

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.reuters.com/", wait_until="domcontentloaded")
    headlines = []
    for i in page.get_by_test_id('TitleHeading').all():
        headlines.append(i.inner_text())
    browser.close()

# with open(f"G:/My Drive/Coding/flask1/test.txt", "w", encoding="utf-8") as f:
#     for i in headlines:
#         f.write( str(datetime.datetime.now()) + i +'\n') 

# c.execute(""" CREATE TABLE IF NOT EXISTS reuters_headlines(timestamp TEXT, news TEXT)
#             """)

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

for i in headlines:
    c.execute("""INSERT INTO reuters_headlines VALUES(?, ?)""" ,(now, i))

### LLM to summarize into another file ###
c.execute(""" CREATE TABLE IF NOT EXISTS reuters_headlines_summary(timestamp TEXT, news TEXT)
            """)
c.execute(""" INSERT INTO reuters_headlines_summary VALUES(?, ?) """, (now, get_news_summary(conn, 'reuters_headlines')
))

conn.commit()

# c.execute("SELECT * FROM reuters_headlines ORDER BY timestamp DESC LIMIT 5")
# print(c.fetchall())


####################### Scraping CNBC Headlines #######################    
url = 'https://www.cnbc.com/'

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded")
    headlines = []
    for i in page.query_selector_all('[class*="headline"]'):
        if i.inner_text != "":
            headlines.append(i.inner_text())

    browser.close()

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# with open('test.txt', "w", encoding="utf-8") as f:
#     for i in headlines:
#         if i != "":
#             f.write( i +'\n') 

c.execute(""" CREATE TABLE IF NOT EXISTS CNBC_headlines(timestamp TEXT, news TEXT)
            """)

for i in headlines:
    c.execute("""INSERT INTO CNBC_headlines VALUES(?, ?)""" ,(now, i))


### LLM to summarize into another file ###
c.execute(""" CREATE TABLE IF NOT EXISTS CNBC_headlines_summary(timestamp TEXT, news TEXT)
            """)
c.execute(""" INSERT INTO CNBC_headlines_summary VALUES(?, ?) """, (now, get_news_summary(conn, 'reuters_headlines')
))


conn.commit()