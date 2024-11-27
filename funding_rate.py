import time  # to simulate a real time data, time loop
from datetime import datetime, timedelta
import numpy as np 
import pandas as pd  
import plotly.express as px  
import streamlit as st  # 🎈 data web app development
import requests
from hyperliquid.info import Info
from streamlit_autorefresh import st_autorefresh



st.set_page_config(
    page_title="Perps vs Spot",
    page_icon="💯",
    layout="wide",
)

def datetime_to_milliseconds(dt):
    return int(dt.timestamp() * 1000)

# Dashboard title
st.title("Perps vs Spot")

info = Info(skip_ws=False)

res = info.meta_and_asset_ctxs()

universe_data = res[0]['universe']
OI_data = res[1]
print(len(universe_data), len(OI_data))

data = [a | b for a, b in zip(universe_data, OI_data)]

print(len(data), len(data[0]))
df1 = pd.json_normalize(data)

available_coins = pd.unique(df1["name"])

# Top-level token filter
token = st.selectbox("Select token", available_coins)

start_date = datetime(2022, 1, 1).date()
end_date = datetime.now().date()
max_days_range = timedelta(days=90)

if "slider_range" not in st.session_state:
    st.session_state.slider_range = (end_date - max_days_range, end_date)

slider_range = st.slider(
    "Select a date range (max 3 months)",
    min_value=start_date,
    max_value=end_date,
    value=st.session_state.slider_range,
    step=timedelta(days=1),
)

selected_start_date, selected_end_date = slider_range

# Check if the selected range exceeds the maximum allowed span
if (selected_end_date - selected_start_date) > max_days_range:
    st.warning("Please select a date range within the maximum allowed span of 3 months. Showing last 3 months from the selected end date")
    selected_start_date = selected_end_date - max_days_range
    st.session_state.slider_range = (selected_start_date, selected_end_date)
    # st.experimental_rerun()  # Rerun the app to update the slider

st.write(f"Showing from {selected_start_date} to {selected_end_date}")

fr_response = info.funding_history(
    name=token, 
    startTime=datetime_to_milliseconds(datetime.combine(selected_start_date, datetime.min.time())), 
    endTime=datetime_to_milliseconds(datetime.combine(selected_end_date, datetime.max.time()))
)

# print(fr_response)
df2 = pd.json_normalize(fr_response)
print(df2.head())

# Creating a single-element container
placeholder = st.empty()
with placeholder.container():
    # fig_col1, fig_col2 = st.columns(2)
    # with fig_col1:
    st.markdown("### Funding Rate Chart")
    if {"time", "fundingRate", "premium"}.issubset(df2.columns):
        if df2["time"].dtype != "datetime64[ns]":
            df2["time"] = pd.to_datetime(df2["time"], unit="ms")
        
        fig = px.line(
            df2, 
            x="time", 
            y=["fundingRate", "premium"], 
            title=f'{token} Funding Rate vs Premium'
        )  

        fig.update_layout(width=1000, height=600, legend_title_text="Legend")  # Adjusted width for better display
        fig.update_yaxes(tickformat=".6f")
        
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Detailed View"):
        st.markdown("### historical funding rates")
        st.dataframe(fr_response)


st.markdown("### Open Interest Chart")
selected_coins = st.multiselect(
    "Select coins to monitor",
    options=available_coins,
    default=['BTC', 'ETH']
)

st.session_state['selected_coins'] = selected_coins

df3 = pd.DataFrame()
# Function to fetch open interest from URL
def fetch_open_interest_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        # st.write(type(response.json()))
        json_data = response.json()
        df3 = pd.json_normalize(json_data['chart_data'])
        # st.write(df3.columns)
        # print("******************************")
        return df3
    except Exception as e:
        st.error(f"error fetching data from url: {e}")
        return []

# URL to fetch open interest data
url = "https://d2v1fiwobg9w6.cloudfront.net/open_interest"

# Function to process fetched open interest data
def process_open_interest_data(data):
    records = []
    for _, entry in data.iterrows():
        # st.write(entry)
        coin = entry['coin']
        if coin in st.session_state['selected_coins']:
            time_str = entry.get('time')
            open_interest = entry.get('open_interest')
            if time_str and open_interest is not None:
                timestamp = pd.to_datetime(time_str)
                records.append({
                    'coin': coin,
                    'time': timestamp,
                    'open_interest': open_interest
                })
    return records

# Fetch and process open interest data
oi_data = fetch_open_interest_from_url(url)
# st.write(oi_data.head())
processed_oi_records = process_open_interest_data(oi_data)
st.session_state['data'] = {}

for coin in selected_coins:
    # Filter records for the current coin
    coin_records = [record for record in processed_oi_records if coin==record['coin']]
    
    if coin_records:
        df_new = pd.DataFrame(coin_records)
        
        if st.session_state['data'].get(coin) is None:
            st.session_state['data'][coin] = df_new
        else:
            st.session_state['data'][coin] = pd.concat(
                [st.session_state['data'][coin], df_new],
                ignore_index=True
            )
        
        if len(st.session_state['data'][coin]) > 1000:
            st.session_state['data'][coin] = st.session_state['data'][coin].tail(1000)


combined_df = pd.DataFrame()
for coin in st.session_state['selected_coins']:
    df = st.session_state['data'].get(coin)
    # df_melt = df.sort_values('time')
    combined_df = pd.concat([combined_df, df])
        
fig = px.line(combined_df,
            x='time',
            y='open_interest',
            color = 'coin',
        )

fig.update_layout(
    title="live open interests",
    xaxis_title="time",
    yaxis_title="open interest",
    hovermode="x unified"
)


# Display the Plotly chart
st.plotly_chart(fig, use_container_width=True)

count = st_autorefresh(
    interval=5 * 1000,  # 5 seconds
    key="data_refresh",
)



#     time.sleep(1)

# perps_response = requests.post("https://api.hyperliquid.xyz/info", headers=headers, json=perps_data)
# fr_response = requests.post("https://api.hyperliquid.xyz/info", headers=headers, json=hist_fr_data)

# if perps_response.status_code == 200:
#     perps_json = perps_response.json()
#     universe_data = perps_json[0]['universe']
#     OI_data = perps_json[1]
#     print(len(universe_data), len(OI_data))
#     data = list(a|b for a,b in zip(universe_data, OI_data))
#     print([0])
#     df1 = pd.json_normalize(data)

#     df1.to_csv('universe_data.csv', index=False)
#     print("Data saved to 'universe_data.csv'")
#     # print(perps_response.json())
# else:
#     print(f"Request failed with status code: {perps_response.status_code}")

# if fr_response.status_code == 200:
#     fr_json = fr_response.json()
#     df2 = pd.json_normalize(fr_json)

#     df2.to_csv('historical_funding_rates.csv', index=False)
#     # print(fr_response.json())
# else:
#     print(f"Request failed with status code: {fr_response.text}")