import time  # to simulate a real time data, time loop
from datetime import datetime, timedelta
import numpy as np  # np mean, np random
import pandas as pd  # read csv, df manipulation
import plotly.express as px  # interactive charts
import streamlit as st  # 🎈 data web app development
import requests
from hyperliquid.info import Info


st.set_page_config(
    page_title="Perps vs Spot",
    page_icon="✅",
    layout="wide",
)

def datetime_to_milliseconds(dt):
    return int(dt.timestamp() * 1000)

# dashboard title
st.title("Perps vs Spot")


info = Info(skip_ws=True)

res = info.meta_and_asset_ctxs()

universe_data = res[0]['universe']
OI_data = res[1]
print(len(universe_data), len(OI_data))
data = list(a|b for a,b in zip(universe_data, OI_data))
print(len(data), len(data[0]))
df1 = pd.json_normalize(data)

print(df1.head)

# top-level token filter
token = st.selectbox("Select token", pd.unique(df1["name"]))

start_date = datetime(2022, 1, 1)
end_date = datetime.now()
max_days_range = timedelta(days=90)
curr_start = start_date
curr_end = end_date

date_range = (start_date, end_date)

if "slider_range" not in st.session_state:
    st.session_state.slider_range = (end_date - max_days_range, end_date)

slider_range = st.slider(
    "select a date range (max 3 months)",
    min_value=start_date,
    max_value=end_date,
    value=st.session_state.slider_range,
    step=timedelta(days=1),
)

if slider_range != st.session_state.slider_range:
    st.session_state.slider_range = slider_range

selected_start_date, selected_end_date = st.session_state.slider_range


if (selected_end_date - selected_start_date) > max_days_range:
    selected_start_date = selected_end_date - max_days_range
    st.session_state.slider_range = (selected_start_date, selected_end_date)

st.write(f"selected start date: {selected_start_date.date()}")
st.write(f"selected end date: {selected_end_date.date()}")

if selected_end_date - selected_start_date > max_days_range:
    st.warning("date range has been adjusted to fit within the maximum allowed span of 3 months.")

fr_response = info.funding_history(name=token, startTime=datetime_to_milliseconds(selected_start_date), endTime=datetime_to_milliseconds(selected_end_date))

print(fr_response)
df2 = pd.json_normalize(fr_response)
print(df2)

# creating a single-element container
placeholder = st.empty()
with placeholder.container():
    fig_col1, fig_col2 = st.columns(2)
    with fig_col1:
        st.markdown("### Funding rate chart")
        if "time" in df2.columns and "fundingRate" in df2.columns and "premium" in df2.columns:
            if df2["time"].dtype != "datetime64[ns]":
                df2["time"] = pd.to_datetime(df2["time"], unit="ms")
            
            fig = px.line(df2, x="time", y=["fundingRate", "premium"], title=f'{token} Funding Rate vs premium')  
    
            fig.update_layout(width=4000, height=600, legend_title_text="Legend")
            fig.update_yaxes(tickformat=".6f")
            
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Detailed Data View")
    st.dataframe(fr_response)
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


# # read csv from a github repo
# dataset_url = "https://raw.githubusercontent.com/Lexie88rus/bank-marketing-analysis/master/bank.csv"

# # read csv from a URL
# @st.experimental_memo
# def get_data() -> pd.DataFrame:
#     return pd.read_csv(dataset_url)

# df = get_data()

# near real-time / live feed simulation
# for seconds in range(200):

    # df["age_new"] = df["age"] * np.random.choice(range(1, 5))
    # df["balance_new"] = df["balance"] * np.random.choice(range(1, 5))

    # # creating KPIs
    # avg_age = np.mean(df["age_new"])

    # count_married = int(
    #     df[(df["marital"] == "married")]["marital"].count()
    #     + np.random.choice(range(1, 30))
    # )

    # balance = np.mean(df["balance_new"])

    # with placeholder.container():

    #     # # create three columns
    #     # kpi1, kpi2, kpi3 = st.columns(3)

    #     # # fill in those three columns with respective metrics or KPIs
    #     # kpi1.metric(
    #     #     label="Age ⏳",
    #     #     value=round(avg_age),
    #     #     delta=round(avg_age) - 10,
    #     # )
        
    #     # kpi2.metric(
    #     #     label="Married Count 💍",
    #     #     value=int(count_married),
    #     #     delta=-10 + count_married,
    #     # )
        
    #     # kpi3.metric(
    #     #     label="A/C Balance ＄",
    #     #     value=f"$ {round(balance,2)} ",
    #     #     delta=-round(balance / count_married) * 100,
    #     # )

    #     # create two columns for charts
    #     fig_col1, fig_col2 = st.columns(2)
    #     with fig_col1:
    #         st.markdown("### Funding rate chart")
    #         # fig = px.density_heatmap(
    #         #     data_frame=df, y="age_new", x="marital"
    #         # )
    #         st.write(fig)
            
    #     # with fig_col2:
    #     #     st.markdown("### Second Chart")
    #     #     fig2 = px.histogram(data_frame=df, x="age_new")
    #     #     st.write(fig2)

    #     st.markdown("### Detailed Data View")
    #     st.dataframe(df2)
    #     time.sleep(1)
