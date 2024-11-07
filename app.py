import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Function to scrape data from the World Bank API
def scrape_worldbank_data(country, ind, start_year, end_year):
    base_url = "http://api.worldbank.org/v2/country/"
    full_url = f"{base_url}{country}/indicator/{ind}?date={start_year}:{end_year}&format=json"
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
def plot_population_data(country_code):
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
    df['MortalityLog'] = np.log1p(df['Mortality'])
    df['NewbornsLog'] = np.log1p(df['Newborns'])
    df['TotalPopLog'] = np.log1p(df['TotalPopulation'])
    df['Mortality_Norm'] = (df['Mortality'] - df['Mortality'].min()) / (df['Mortality'].max() - df['Mortality'].min())
    df['TotalPopulation_Norm'] = (df['TotalPopulation'] - df['TotalPopulation'].min()) / (df['TotalPopulation'].max() - df['TotalPopulation'].min())
    df['Newborns_Norm'] = (df['Newborns'] - df['Newborns'].min()) / (df['Newborns'].max() - df['Newborns'].min())

    plt.figure(figsize=(10, 6))
    plt.plot(df['Year'], df['Mortality_Norm'], marker='o', label='Mortality Normalized')
    plt.plot(df['Year'], df['TotalPopulation_Norm'], marker='o', label='Total Population Normalized')
    plt.plot(df['Year'], df['Newborns_Norm'], marker='o', label='Total Newborns Normalized')
    plt.title(f'Demographics in {df["Country"][0]} ({df["Year"].min()}-{df["Year"].max()})')
    plt.xlabel("Year")
    plt.ylabel("Normalized Values")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    st.pyplot(plt)

# Streamlit app layout and logic
def main():
    st.title("World Bank Population Data Viewer")
    st.write("Select a country code to view population growth and related metrics.")

    # Country code input
    country_code = st.text_input("Enter a 3-letter ISO country code (e.g., USA, IND, BRA):", value="USA")

    # Generate plot button
    if st.button("Generate Plot"):
        st.write(f"Fetching data for country code: {country_code}")
        plot_population_data(country_code)

if __name__ == "__main__":
    main()
