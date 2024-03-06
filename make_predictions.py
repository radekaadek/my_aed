# load h2o model and make predictions
import h2o
import os
import json
import pandas as pd

# initialize h2o
h2o.init()

with open('model_path.txt', 'r') as f:
    model_path = f.read().strip()

# load jar model
saved_model = h2o.load_model(model_path)

my_local_model = h2o.download_model(saved_model)

my_uploaded_model = h2o.upload_model(my_local_model)


target = 'OHCA'
# Read the data
main_df = pd.read_csv('./data/main_hexagon_df.csv')
# read target csv
target_df = pd.read_csv('./data/target.csv')
# set index tame to hex_id
input_data = target_df.copy()
# make predictions
# drop unnamed column
input_data.drop('Unnamed: 0', axis=1, inplace=True)
data = h2o.H2OFrame(input_data)
predictions = my_uploaded_model.predict(data)
# convert to pandas
predictions = predictions.as_data_frame()

# add predictions['predict'] to target_df
target_df['OHCA'] = predictions['predict']
# appyl np.maximum(0, x) to OHCA
target_df['OHCA'] = target_df['OHCA'].apply(lambda x: max(0, x))
# set unnamed to hex_id and set it as the index
target_df.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
target_df.set_index('hex_id', inplace=True)
# save as csv
target_df.to_csv('./data/predictions.csv')

# create a {"hex_id": "OHCA"} dictionary
predictions = target_df.to_dict()['OHCA']
# check if the results folder exists
if not os.path.exists('./results'):
    os.makedirs('./results')
# save predictions as json
with open('./results/results.json', 'w') as f:
    json.dump(predictions, f)
# shutdown h2o
h2o.cluster().shutdown()

