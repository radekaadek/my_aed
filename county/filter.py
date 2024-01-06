import pandas as pd

# data source: https://data.marincounty.org/Public-Health/Emergency-Medical-Service-EMS-Incidents/swth-izpe/about_data

# read the file, on stdin as a csv
df = pd.read_csv('county_to_filter.csv', encoding='latin-1')
# filter column cardiac_type if it contains 'Cardiac Arrest' or the column cause contains 'Cardiac Arrest'
df = df[df['cardiac_type'].str.contains('Cardiac Arrest') | df['cause'].str.contains('Cardiac Arrest')]

# drop empty columns
# get the columns that are empty
empty_cols = [col for col in df.columns if df[col].isnull().all()]
# drop empty columns
df.drop(empty_cols,
        axis=1,
        inplace=True)
# write the filtered data to a new file
df.to_csv('county_filtered.csv', index=False)
