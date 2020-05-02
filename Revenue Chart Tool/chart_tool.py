import sys
import pandas as pd
import altair as alt
import datetime
import numpy as np
import streamlit as st
from streamlit import caching
import os
import tkinter as tk
from tkinter import filedialog  


YEAR_OPTIONS = list(range(2012,2021))
MONTH_OPTIONS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
month_dict = {month : i + 1 for i, month in enumerate(MONTH_OPTIONS)}

@st.cache
def open_file():
    # Get a file 
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.askopenfilename(master=root)
    
    if file_path[-3:] in ['txt', 'csv']:
        df = pd.read_csv(file_path, sep=None)
    elif 'xls' in file_path[-4:]:
        df = pd.read_excel(file_path)
    else:
        raise ValueError('Not valid file for upload, only CSV and Excel currently supported')
                         
    # Transform columns
    df.columns = [''.join([c for c in col.lower() if c.isalnum()]) for col in df.columns]
    cols = list(df.columns)
    for i, col in enumerate(cols):
        if 'amount' in col:
            cols[i] = 'amount'
        elif 'date' in col:
            cols[i] = 'date'
        else:
            pass
    df.columns = cols
    df.date = pd.to_datetime(df.date)
    df.amount = pd.to_numeric(df.amount)
        
    return df

@st.cache
def create_daily_df(df):
    ## Clean data
    tmp_df = df.copy(deep=True)
    daily_df = df.loc[tmp_df['date'] >= datetime.datetime(2012,1,1), ['date', 'amount']].groupby('date').sum()
    dates = pd.date_range(start='1/1/2012', end='12/31/2020')
    daily_df = daily_df.reindex(index = dates)
    daily_df.fillna(0, inplace=True)
    daily_df['year'] = daily_df.index.year
    daily_df['month'] = daily_df.index.month
    daily_df['Day of Year'] = daily_df.index.dayofyear
    daily_df['Annual Donations'] = daily_df.groupby('year')['amount'].cumsum()
    daily_df['Monthly Donations'] = daily_df.groupby(['year','month'])['amount'].cumsum()
    daily_df.loc[daily_df.index>=datetime.datetime(2020,2,21), ['Annual Donations', 'Monthly Donations']] = np.nan
    daily_df = daily_df[daily_df.year >= 2012].copy(deep=True)
    
    return daily_df


def create_annual_chart(df, y1, y2):
    tmp_df = df.copy(deep=True)
    tmp_df = tmp_df[(tmp_df.year == y1) | (tmp_df.year == y2)]
    # Create chart
    chart = (
        alt.Chart(tmp_df)
        .mark_line()
        .encode(
            x=alt.X("Day of Year:Q"
                   , scale=alt.Scale(domain=(1, 366))
                   ),
            y=alt.Y("Annual Donations"),
            color="year:N",
            
        )
    )
    
    return chart


def create_monthly_chart(df, m1, m2, y1, y2):
    tmp_df = df.copy(deep=True)
    tmp_df['month_year'] = tmp_df.apply(lambda row: f'{int(row.month)}-{int(row.year)}', axis=1)
    tmp_df = tmp_df[(tmp_df.month_year == f'{m1}-{y1}') | (tmp_df.month_year == f'{m2}-{y2}')]
    min_day = tmp_df.index.dayofyear.min()
    tmp_df['Day of Month'] = tmp_df.index.dayofyear - min_day
    chart = (
        alt.Chart(tmp_df)
        .mark_line()
        .encode(
            x=alt.X("Day of Month:Q"
            , scale=alt.Scale(domain=(1,31))
            ),
            y=alt.Y("Monthly Donations"),
            color="year:N"
        )
    )
    
    return chart


# Sidebar Creation
# Load data retrieved from the OS
st.sidebar.markdown("Click button below to upload a new file.")
if st.sidebar.button("Upload File"):
    caching.clear_cache()
    df = open_file()
else:
    df = open_file()   
df = open_file() 
daily_df = create_daily_df(df)

# Ask user if they want to do YoY or MoM
choice = st.sidebar.radio("What type of chart would you like to create?", ("Year over Year", "Month over Month"))


# Create charts
if choice == "Year over Year":
    st.write("This tool generates a year over year chart to compare the daily revenue of one year to another")
    
    # Create chart
    y1 = st.selectbox("Year", YEAR_OPTIONS, len(YEAR_OPTIONS)-1)
    y2 = st.selectbox("Year to Compare", YEAR_OPTIONS, len(YEAR_OPTIONS)-2)
    chart = create_annual_chart(daily_df, y1, y2)
    st.altair_chart(chart, use_container_width=True)
    
elif choice == "Month over Month":

    y1 = st.selectbox("Year 1", YEAR_OPTIONS, len(YEAR_OPTIONS)-1)
    y2 = st.selectbox("Year 2", YEAR_OPTIONS, len(YEAR_OPTIONS)-2)
    m = st.selectbox("Month", MONTH_OPTIONS, 0)
    m1 = m2 = month_dict[m]
    chart = create_monthly_chart(daily_df, m1, m2, y1, y2)
    st.write(f"Chart comparing {m} revenue between {y1} and {y2}")
    st.altair_chart(chart, use_container_width=True)
    
           
# Option to open file
if st.checkbox("Show File"):
    st.dataframe(df)
