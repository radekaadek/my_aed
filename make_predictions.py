# load h2o model and make predictions
import h2o
import pandas as pd

# initialize h2o
h2o.init()

# load jar model
model_path = "StackedEnsemble_BestOfFamily_1_AutoML_1_20240108_174135"
saved_model = h2o.load_model(model_path)

my_local_model = h2o.download_model(saved_model)

my_uploaded_model = h2o.upload_model(my_local_model)

# load data
data_path = "warszawa_osm.csv"
input_data = pd.read_csv(data_path)
# input_data.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
# print cols
# make predictions
data = h2o.H2OFrame(input_data)
predictions = my_uploaded_model.predict(data)
# convert to pandas
predictions = predictions.as_data_frame()
# add to warszawa_osm.csv and save as predictions.csv
data = data.as_data_frame()
data['predictions'] = predictions
# apply max(0, predictions) to predictions
data['predictions'] = data['predictions'].apply(lambda x: max(0, x))
# set index
# add hex_id column from warszawa_osm.csv and make it index
data['hex_id'] = input_data['Unnamed: 0']
data.set_index('hex_id', inplace=True)
# save to csv
data.to_csv('predictions.csv')
