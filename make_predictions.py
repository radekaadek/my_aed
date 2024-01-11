# load h2o model and make predictions
import h2o
import pandas as pd

# initialize h2o
h2o.init()

# load jar model
model_path = "XGBoost_grid_1_AutoML_1_20240111_185033_model_60"
saved_model = h2o.load_model(model_path)

my_local_model = h2o.download_model(saved_model)

my_uploaded_model = h2o.upload_model(my_local_model)


target = 'OHCA'
# Read the data
main_df = pd.read_csv('main_hexagon_df.csv')
# read target csv
target_df = pd.read_csv('target.csv')
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
# set unnamed to hex_id and set it as the index
target_df.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
target_df.set_index('hex_id', inplace=True)
print(target_df.head())
# save as csv
target_df.to_csv('predictions.csv')
