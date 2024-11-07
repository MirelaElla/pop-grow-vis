import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Function to fetch all country names and codes
def fetch_country_list():
    url = "http://api.worldbank.org/v2/country?format=json&per_page=300"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if len(data) > 1:
            countries = {item["name"]: item["id"] for item in data[1]}
            return countries
    st.error("Failed to fetch country list.")
    return {}

# Function to scrape data from the World Bank API
def scrape_worldbank_data(country_code, ind, start_year, end_year):
    base_url = "http://api.worldbank.org/v2/country/"
    full_url = f"{base_url}{country_code}/indicator/{ind}?date={start_year}:{end_year}&format=json"
    response = requests.get(full_url)
    if response.status_code == 200:
        data = response.json()
        if len(data) > 1:
            return [(int(item["date"]), item["value"], item["country"]["value"]) for item in data[1] if item["value"] is not None]
        else:
            return []
    else:
        st.error("Failed to retrieve data from the World Bank API.")
        return []

# Function to plot population growth and related metrics
def plot_population_data(country_code, country_name):
    mortality = "SP.DYN.CDRT.IN"
    newborns = "SP.DYN.CBRT.IN"
    totpop = "SP.POP.TOTL"
    start_year = "1950"
    end_year = "2024"

    mortality_data = scrape_worldbank_data(country_code, mortality, start_year, end_year)
    totpop_data = scrape_worldbank_data(country_code, totpop, start_year, end_year)
    newborn_data = scrape_worldbank_data(country_code, newborns, start_year, end_year)

    if not mortality_data or not totpop_data or not newborn_data:
        st.error("No data available for the selected country.")
        return

    mortality_df = pd.DataFrame(mortality_data, columns=['Year', 'Mortality', "Country"])
    newborn_df = pd.DataFrame(newborn_data, columns=['Year', 'Newborns', "Country"])
    totpop_df = pd.DataFrame(totpop_data, columns=['Year', 'TotalPopulation', "Country"])

    combined_df = mortality_df.merge(newborn_df, on='Year').merge(totpop_df, on='Year')
    combined_df.Mortality = (combined_df.Mortality / 1000) * combined_df.TotalPopulation
    combined_df.Newborns = (combined_df.Newborns / 1000) * combined_df.TotalPopulation

    df = combined_df
    df['Mortality_Norm'] = (df['Mortality'] - df['Mortality'].min()) / (df['Mortality'].max() - df['Mortality'].min())
    df['TotalPopulation_Norm'] = (df['TotalPopulation'] - df['TotalPopulation'].min()) / (df['TotalPopulation'].max() - df['TotalPopulation'].min())
    df['Newborns_Norm'] = (df['Newborns'] - df['Newborns'].min()) / (df['Newborns'].max() - df['Newborns'].min())

    # Create figure and axes with transparent background
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_alpha(0)  # Ensure full transparency
    ax.set_facecolor('none')

    # Plot lines with custom colors
    ax.plot(df['Year'], df['Mortality_Norm'], marker='o', label='Mortality (Normalized)', linewidth=2, color='#FF6F61')
    ax.plot(df['Year'], df['TotalPopulation_Norm'], marker='o', label='Total Population (Normalized)', linewidth=2, color='#6BDBE6')
    ax.plot(df['Year'], df['Newborns_Norm'], marker='o', label='Newborns (Normalized)', linewidth=2, color='#F7D154')

    # Customize grid, ticks, and labels for readability
    ax.grid(color='#444', linestyle='--', linewidth=0.5)
    ax.spines['bottom'].set_color('#888')
    ax.spines['left'].set_color('#888')
    ax.tick_params(colors='#ECECEC')  # Light gray tick labels
    ax.xaxis.label.set_color('#ECECEC')  # Light gray X-axis label
    ax.yaxis.label.set_color('#ECECEC')  # Light gray Y-axis label
    ax.title.set_color('#ECECEC')  # Light gray title

    # Labels and title
    ax.set_title(f'Demographics in {country_name} ({df["Year"].min()}-{df["Year"].max()})', fontsize=16, pad=20)
    ax.set_xlabel("Year", fontsize=14)
    ax.set_ylabel("Normalized Values", fontsize=14)

    # Legend with light text
    legend = ax.legend(fontsize=12, facecolor='none', edgecolor='none')
    for text in legend.get_texts():
        text.set_color('#ECECEC')  # Light gray legend text

    # Display the plot in Streamlit
    st.pyplot(fig)

# Streamlit app layout and logic
def main():
    st.title("World Bank Population Data Viewer")
    st.write("Select a country to view population growth and related metrics.")

    # Fetch the country list and allow selection
    countries = fetch_country_list()
    if not countries:
        st.stop()

    country_name = st.selectbox("Select a country:", list(countries.keys()))
    country_code = countries[country_name]

    # Generate plot button
    if st.button("Generate Plot"):
        st.write(f"Fetching data for {country_name}...")
        plot_population_data(country_code, country_name)

if __name__ == "__main__":
    main()