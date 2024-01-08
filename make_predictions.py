# load h2o model and make predictions
import h2o
import pandas as pd

# initialize h2o
h2o.init()

# load jar model
model_path = "h2o-genmodel.jar"
saved_model = h2o.load_model(model_path)

my_local_model = h2o.download_model(model_path)

# load data
data_path = "warszawa_osm.csv"
data = pd.read_csv(data_path)

# make predictions
data = h2o.H2OFrame(data)
predictions = my_local_model.predict(data)
predictions_df = predictions.as_data_frame()
data_df = data.as_data_frame()
data_df['predictions'] = predictions_df
data_df.to_csv('predictions.csv')
