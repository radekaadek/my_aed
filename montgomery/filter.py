import pandas as pd

# data source: https://www.kaggle.com/datasets/mchirico/montcoalert

# Read in the data
df = pd.read_csv('mtgmry_unfiltered.csv')

# filter by contains 'CARDIAC ARREST'
df = df[df['title'].str.contains('CARDIAC ARREST')]

print(df.head())
print(len(df))

# Write to csv
df.to_csv('mtgmry_filtered.csv', index=False)
