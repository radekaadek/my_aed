import io
import pandas as pd
import requests
import numpy as np
import h3
from os import listdir

# check for the vbohcar.xlsx file in the current directory
if 'VBOHCAR.xlsx' in listdir():
        # read the third sheet of the excel file
    vb_ohca_in = pd.read_excel('VBOHCAR.xlsx', sheet_name=3)
else:
    # clone the excel file from github
    url = 'https://github.com/INFORMSJoC/2020.1022/blob/master/results/VBOHCAR.xlsx?raw=true'
    file = requests.get(url)
    file_bytes = io.BytesIO(file.content)
    # read the third sheet of the excel file
    vb_ohca_in = pd.read_excel(file_bytes, sheet_name=3)

def hexid_ohca(df: pd.DataFrame, lat_col: str, lon_col: str, res: int = 9) -> pd.DataFrame:
    """
    This function takes a dataframe of OHCA incidents and returns a dictionary
    with the hex_id as the key and the count
    of OHCA incidents as the value.
    :param df: a dataframe of OHCA incidents
    :param lat_col: the name of the column with the latitude values
    :param lon_col: the name of the column with the longitude values
    :param res: the resolution of the hex_id
    :return: a dictionary with the hex_id as the key and the count of OHCA incidents as the value
    """
    # create a dictionary to hold the hex_id and the count of OHCA incidents
    hexid_ohca_cnt = {}
    for _, row in df.iterrows():
        # get the hex_id for each row
        hex_id = h3.latlng_to_cell(np.float64(row[lat_col]), np.float64(row[lon_col]), res)
        # if the hex_id is not in the dictionary, add it
        if hex_id not in hexid_ohca_cnt:
            hexid_ohca_cnt[hex_id] = 0
        # increment the count of OHCA in the hex_id
        hexid_ohca_cnt[hex_id] += 1
    
    return hexid_ohca_cnt


hexid_ohca_cnt = hexid_ohca(vb_ohca_in, 'Latitude', 'Longitude', 9)

# create a dataframe from the dictionary with the hex_id as the index
main_ohca_df = pd.DataFrame.from_dict(hexid_ohca_cnt, orient='index', columns=['OHCA'])

mtgmry_ohca_df = pd.read_csv('montgomery/mtgmry_unfiltered.csv')
# filter by 'title' containing 'CARDIAC ARREST'
mtgmry_ohca_df = mtgmry_ohca_df[mtgmry_ohca_df['title'].str.contains('CARDIAC ARREST')]
# timeStamp contatins 2017 2018 2019
mtgmry_ohca_df = mtgmry_ohca_df[mtgmry_ohca_df['timeStamp'].str.contains('2017|2018|2019')]
# create a dictionary to hold the counts of OHCA in each hex_id
hexid_ohca_cnt = {}
# iterate through the rows of the dataframe
for i, row in mtgmry_ohca_df.iterrows():
    # get the hex_id for each row
    hex_id = h3.latlng_to_cell(np.float64(row['lat']), np.float64(row['lng']), 9)
    # if the hex_id is not in the dictionary, add it
    if hex_id not in hexid_ohca_cnt:
        hexid_ohca_cnt[hex_id] = 0
    # increment the count of OHCA in the hex_id
    hexid_ohca_cnt[hex_id] += 1

mtgmry_ohca_df = pd.DataFrame.from_dict(hexid_ohca_cnt, orient='index', columns=['OHCA'])
# add the OHCA count to the main dataframe
main_ohca_df = pd.concat([main_ohca_df, mtgmry_ohca_df], ignore_index=False, axis=0)

# read cinncinati data
cinncinati_ohca_df = pd.read_csv('cincinnati/Cincinnati_Fire_Incidents__CAD___including_EMS__ALS_BLS_.csv')
# remove rows with NaN values in 'LATITUDE_X' or 'LONGITUDE_X'
cinncinati_ohca_df.dropna(subset=['LATITUDE_X', 'LONGITUDE_X'], inplace=True)
# filter by 'INCIDENT_TYPE_DESC' containing 'CARDIAC' and STROKE (CVA) / CFD_INCIDENT_TYPE_GROUP containing 'CARDIAC'
# first fill the NaN values with empty strings
cinncinati_ohca_df['INCIDENT_TYPE_DESC'].fillna('', inplace=True)
cinncinati_ohca_df['CFD_INCIDENT_TYPE_GROUP'].fillna('', inplace=True)
cinncinati_ohca_df = cinncinati_ohca_df[cinncinati_ohca_df['CFD_INCIDENT_TYPE_GROUP'].str.contains('CARDIAC')]
# filter CREATE_TIME_INCIDENT containing 2017 2018 2019
cinncinati_ohca_df = cinncinati_ohca_df[cinncinati_ohca_df['CREATE_TIME_INCIDENT'].str.contains('2017|2018|2019')]

# create a dictionary to hold the counts of OHCA in each hex_id
hexid_ohca_cin = hexid_ohca(cinncinati_ohca_df, 'LATITUDE_X', 'LONGITUDE_X', 9)
# create a dataframe from the dictionary with the hex_id as the index
cinncinati_ohca_df = pd.DataFrame.from_dict(hexid_ohca_cin, orient='index', columns=['OHCA'])
# add the OHCA count to the main dataframe
main_ohca_df = pd.concat([main_ohca_df, cinncinati_ohca_df], ignore_index=False, axis=0)

# now read virginia_beach data
main_hexagon_df = pd.read_csv('virginia_beach_osm.csv')
main_hexagon_df.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
# pivot the dataframe to have the hex_id as the index
main_hexagon_df.set_index('hex_id', inplace=True)

# add montgomery
mtgmry_hexagon_df = pd.read_csv('montgomery_osm.csv')
mtgmry_hexagon_df.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
# pivot the dataframe to have the hex_id as the index
mtgmry_hexagon_df.set_index('hex_id', inplace=True)
main_hexagon_df = pd.concat([main_hexagon_df, mtgmry_hexagon_df], ignore_index=False, axis=0)

# add the OHCA count to the main dataframe
main_hexagon_df = pd.concat([main_hexagon_df, main_ohca_df], ignore_index=False, axis=1)
# save to a csv file

# add cinncinati
cinncinati_hexagon_df = pd.read_csv('cincinnati_osm.csv')
cinncinati_hexagon_df.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
# pivot the dataframe to have the hex_id as the index
cinncinati_hexagon_df.set_index('hex_id', inplace=True)
main_hexagon_df = pd.concat([main_hexagon_df, cinncinati_hexagon_df], ignore_index=False, axis=0)
# fill the NaN values with 0
main_hexagon_df.fillna(0, inplace=True)
main_hexagon_df.to_csv('main_hexagon_df.csv')

# read the csv file
poland_df = pd.read_csv('warszawa_osm.csv')
# set unnamed column name to hex_id
poland_df.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
# pivot the dataframe to have the hex_id as the index
poland_df.set_index('hex_id', inplace=True)
# delete columns not in training data
main_cols = list(main_hexagon_df.columns)
poland_cols = list(poland_df.columns)
for col in poland_cols:
    if col not in main_cols:
        del poland_df[col]
# fill the NaN values with 0

# drop columns in main_hexagon_df that are not in poland_df
main_cols = list(main_hexagon_df.columns)
poland_cols = list(poland_df.columns)
for col in main_cols:
    if col not in poland_cols and col != 'OHCA':
        del main_hexagon_df[col]

# now split by 5%s
procent = 0.05
main_hexagon_df['lvl2'] = 0
for i in np.arange(procent, 1, procent):
    main_hexagon_df.loc[main_hexagon_df['OHCA'] > main_hexagon_df['OHCA'].quantile(i), 'lvl2'] = np.round((i+procent)*100)
# draw a bar chart of OHCA counts by hexagon level
# sort by number in the front
main_hexagon_df['lvl2'].value_counts().sort_index().plot(kind='bar')

# now convert them to 0, 1, 2, 3, 4
main_hexagon_df['lvl2'] = main_hexagon_df['lvl2'].replace(0, 0)
main_hexagon_df['lvl2'] = main_hexagon_df['lvl2'].replace(75, 1)
main_hexagon_df['lvl2'] = main_hexagon_df['lvl2'].replace(90, 2)
main_hexagon_df['lvl2'] = main_hexagon_df['lvl2'].replace(95, 3)
main_hexagon_df['lvl2'] = main_hexagon_df['lvl2'].replace(100, 4)

# drop the OHCA column :O
del main_hexagon_df['OHCA']

# save as main_hexagon_df.csv
main_hexagon_df.to_csv('main_hexagon_df.csv')
