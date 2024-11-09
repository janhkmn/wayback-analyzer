import streamlit as st
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter
import sys
import os
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

from data.requests import gpt_request, wayback_get_captures, wayback_get_content

st.title("Website Evolution Analysis with Wayback Machine")
url = st.text_input("Analyze URL", placeholder="https://www.tarohealth.com")

selected_years = st.multiselect(
    "Select years to analyze",
    options=[2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],  # Adjust to other years as necessary
    default=[2022, 2023, 2024]
)

if st.button("Run Analysis") and url:

    capture_dates = []
    captured_content = {}

    with st.spinner("Fetching data from Wayback Machine..."):
        for year in selected_years:
            calendar = wayback_get_captures(url, year)
            if "items" in calendar:
                # Get the last valid snapshot date with status 200
                last_valid_date = [x["date"] for x in calendar["items"] if x["status_code"] == 200][-1]
                capture_dates.append(last_valid_date)

                st.write(f"Fetching content for {last_valid_date}...")
                r = wayback_get_content(url, last_valid_date)
                bs = BeautifulSoup(r["content"], 'html.parser')
                converted_to_md = MarkdownConverter().convert_soup(bs)
                captured_content[last_valid_date] = converted_to_md

    for date, content in captured_content.items():
        st.write(f"Capture Date: {date}, Content Length: {len(content)} characters")

    prompt = f"""
        Here is the markdown of the website {url}. 
        I'm an investor and trying to understand how the company has evolved, particularly if there have been major pivots or narrative shifts.

        Could you provide a detailed summary of the changes you're seeing (max 2000 characters), as well as summarize each point-in-time (less than 400 characters for each)?
    """

    for date, content in captured_content.items():
        prompt += f"\n\n Year {date} \n {content}"

    with st.spinner("Processing with GPT..."):
        answer = gpt_request(prompt, max_tokens=10000, model="gpt-4o")

    st.markdown(answer)
