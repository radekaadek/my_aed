"""
This script downloads OHCA data from sources and adds them to the main dataframe
It also adds the neighbors to the data
"""

import io
import pandas as pd
import requests
import numpy as np
import h3
import os

target = 'predictions'

# check for the vbohcar.xlsx file in the /data directory
if 'VBOHCAR.xlsx' in os.listdir('data'):
        # read the third sheet of the excel file
    vb_ohca_in = pd.read_excel('./data/VBOHCAR.xlsx', sheet_name=3)
else:
    # clone the excel file from github
    url = 'https://github.com/INFORMSJoC/2020.1022/blob/master/results/VBOHCAR.xlsx?raw=true'
    file = requests.get(url)
    file_bytes = io.BytesIO(file.content)
    # save the file to the current directory
    with open('./data/VBOHCAR.xlsx', 'wb') as f:
        f.write(file_bytes.read())
    # read the third sheet of the excel file
    vb_ohca_in = pd.read_excel(file_bytes, sheet_name=3)

def hexid_ohca(df: pd.DataFrame, lat_col: str, lon_col: str, res: int = 9) -> dict:
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

file_path = './data/mtgmry_unfiltered.csv'
# check if montgomery data is in the data directory
if 'mtgmry_unfiltered.csv' not in os.listdir('data'):
    # download the montgomery data and save it to the data directory
    # set KAGGLE_USERNAME and KAGGLE_KEY environment variables {"username":"ardfessdx","key":"f2c9378c38080c30a3649d2abe658a0d"}
    # create a file in ~/.kaggle/kaggle.json with the username and key
    with open(os.path.expanduser('~/.kaggle/kaggle.json'), 'w') as f:
        f.write('{"username":"ardfessdx","key":"f2c9378c38080c30a3649d2abe658a0d"}')
    os.system('cd data && kaggle datasets download -d mchirico/montcoalert --unzip')
    # rename the file to mtgmry_unfiltered.csv
    os.system(f'mv ./data/911.csv {file_path}')
mtgmry_ohca_df = pd.read_csv(file_path)

# filter by 'title' containing 'CARDIAC ARREST'
mtgmry_ohca_df = mtgmry_ohca_df[mtgmry_ohca_df['title'].str.contains('CARDIAC ARREST')]
# timeStamp contatins 2017 2018 2019
mtgmry_ohca_df = mtgmry_ohca_df[mtgmry_ohca_df['timeStamp'].str.contains('2016|2017|2018|2019')]
# create a dictionary to hold the counts of OHCA in each hex_id
hexid_ohca_cnt = hexid_ohca(mtgmry_ohca_df, 'lat', 'lng', 9)
# multiply all of the values by 3/4
for hex_id in hexid_ohca_cnt:
    hexid_ohca_cnt[hex_id] = hexid_ohca_cnt[hex_id] * 3 / 4
mtgmry_ohca_df = pd.DataFrame.from_dict(hexid_ohca_cnt, orient='index', columns=['OHCA'])
# add the OHCA count to the main dataframe
main_ohca_df = pd.concat([main_ohca_df, mtgmry_ohca_df], ignore_index=False, axis=0)


# read cinncinati data
if 'Cincinnati_Fire_Incidents__CAD___including_EMS__ALS_BLS_.csv' in os.listdir('data'):
    cinncinati_ohca_df = pd.read_csv('./data/Cincinnati_Fire_Incidents__CAD___including_EMS__ALS_BLS_.csv')
else:
    raise NotImplementedError('Automatical downloading of the Cincinnati data is not implemented yet. Please\
                              download the data manually and place it in the data directory from:\
                              https://data.cincinnati-oh.gov/Safety/Cincinnati-Fire-Incidents-CAD-including-EMS-ALS-BL/vnsz-a3wp/data\
                              and put it in the data directory as Cincinnati_Fire_Incidents__CAD___including_EMS__ALS_BLS_.csv')
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
cincin_hex_ohca = hexid_ohca(cinncinati_ohca_df, 'LATITUDE_X', 'LONGITUDE_X', 9)
# create a dataframe from the dictionary with the hex_id as the index
cinncinati_ohca_df = pd.DataFrame.from_dict(cincin_hex_ohca, orient='index', columns=['OHCA'])
# add the OHCA count to the main dataframe
main_ohca_df = pd.concat([main_ohca_df, cinncinati_ohca_df], ignore_index=False, axis=0) # <- check this


os.system('./neighbourer/bin/main < ./data/osm_data.csv > ./data/osm_data_osm_neighbours.csv')
os.system('./neighbourer/bin/main < ./data/warszawa_osm.csv > ./data/warszawa_osm_osm_neighbours.csv')

# now read virginia_beach data
main_hexagon_df = pd.read_csv('./data/osm_data_osm_neighbours.csv')
# drop the unnamed columns
main_hexagon_df.drop(columns=['Unnamed: 0'], inplace=True)
# rename the columns by shifting them to the left
# print columns that sum to 0
print(list(main_hexagon_df.columns))
print(main_hexagon_df.head())
# print the sums of the first 10 columns
print(main_hexagon_df.iloc[:, 0:10].sum())
# pivot the dataframe to have the hex_id as the index
main_hexagon_df['OHCA'] = np.float32(0)

# add the OHCA counts to the main DataFrame
for hex_id, ohca in main_ohca_df.iterrows():
    if hex_id in main_hexagon_df.index:
        main_hexagon_df.loc[hex_id, 'OHCA'] = ohca['OHCA']


# Now for the target OSM data

# read the csv file
poland_df = pd.read_csv('./data/warszawa_osm_osm_neighbours.csv')
# drop the unnamed columns
poland_df.drop(columns=['Unnamed: 0'], inplace=True)

# delete columns not in training data
poland_cols = list(poland_df.columns)
main_cols = list(main_hexagon_df.columns)
for col in poland_cols:
    if col not in main_cols:
        del poland_df[col]
# drop columns in main_hexagon_df that are not in poland_df
for col in main_cols:
    if col not in poland_cols and col != 'OHCA':
        del main_hexagon_df[col]

# fill NaN values with 0
main_hexagon_df.fillna(0, inplace=True)

# delete rows with all columns equal to 0
main_hexagon_df = main_hexagon_df[(main_hexagon_df.T != 0).any()]
# save as main_hexagon_df.csv
poland_df.to_csv('./data/target.csv')
main_hexagon_df.to_csv('./data/main_hexagon_df.csv')

