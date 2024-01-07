import time
import numpy as np
import pandas as pd
# geocoding

# data source: https://data.marincounty.org/Public-Health/Emergency-Medical-Service-EMS-Incidents/swth-izpe/about_data

# read the file, on stdin as a csv
df = pd.read_csv('Emergency_Medical_Service__EMS__Incidents_20240107.csv', encoding='latin-1')
# dates are in the format 12/16/2020 03:35:00 PM
# make a date column with Time Call Was Received
df['date'] = pd.to_datetime(df['Time Call Was Received'])
# try to fill in the blanks with columns in order: Time Vehicle was Dispatched, Time Vehicle was en Route to Scene, Time Arrived on Scene, Time Arrived at Patient, Time Departed from the Scene, Time Arrived to Next Destination (i.e., Hospital)
cols = ['Time Vehicle was Dispatched', 'Time Vehicle was en Route to Scene', 'Time Arrived on Scene', 'Time Arrived at Patient', 'Time Departed from the Scene', 'Time Arrived to Next Destination (i.e., Hospital)']
for col in cols:
    df['date'] = df.apply(lambda row: row['date'] if pd.notnull(row['date']) else pd.to_datetime(row[col]), axis=1)
df = df.dropna(subset=['date'])
# add lat and lon columns
df['lat'] = df['Incident Latitude']
df['lon'] = df['Incident Longitude']

# filter by if Protocol Used by EMS Personnel or Primary Impression or Primary Injury has 'Cardi' in it
df = df[df['Protocol Used by EMS Personnel'].str.contains('Cardi', na=False) | df['Primary Impression'].str.contains('Cardi', na=False) | df['Primary Injury'].str.contains('Cardi', na=False)]


# try to geocode missing lat and lon with Incident Address, Incident City, Incident ZIP Postal, Incident County
# geocoding using google
import requests
import json



def geocode(address, api_key):
    url = f'https://geocode.maps.co/search?q={address}&api_key={api_key}'
    r = requests.get(url)
    print(r.text)
    # example response:
    # [{"place_id":339832432,"licence":"Data ┬ę OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright","osm_type":"way","osm_id":786174677,"boundingbox":["37.9413832","37.9414714","-122.4846035","-122.4844751"],"lat":"37.9414197","lon":"-122.48453930069466","display_name":"San Quentin Post Office, 1, Main Street, San Quentin, Marin County, California, 94964, United States","class":"amenity","type":"post_office","importance":0.51001}]
    # remove first and last characters
    data = json.loads(r.text)
    if len(data) == 0:
        return None, None
    return data[0]['lat'], data[0]['lon']

address_cols = ['Incident Address', 'Incident ZIP Postal', 'Incident County']
api_key = ''

with open('apikey.txt', 'r') as f:
    api_key = f.read()
for _, row in df.iterrows():
    if pd.isnull(row['lat']) or pd.isnull(row['lon']):
        if pd.isnull(row['Incident Address']):
            continue
        if pd.isnull(row['Incident ZIP Postal']):
            continue
        if pd.isnull(row['Incident County']):
            continue
        city = None
        # not null
        if pd.notnull(row['Incident City']):
            city = row['Incident City']
        address = ', '.join([str(row[col]) for col in address_cols]) + ' County'
        if city is not None:
            address += ', ' + city
        # delete nan values
        address = address.replace(', nan', '')
        print(f"Adress: {address}")
        # if address is empty, skip
        if address == '':
            continue
        lat, lon = geocode(address, api_key)
        # wait to avoid rate limiting
        time.sleep(1)
        if lat is not None and lon is not None:
            df.loc[_, 'lat'] = np.float64(lat)
            df.loc[_, 'lon'] = np.float64(lon)

# add lat and lon where missing

df = df.dropna(subset=['lat', 'lon'])

# write the file as a csv
df.to_csv('date_loc_county_cardi.csv', index=False)
