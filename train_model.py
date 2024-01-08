import pandas as pd
import h2o
from h2o.automl import H2OAutoML

# Read the defata
main_df = pd.read_csv('main_hexagon_df.csv')

main_df.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
main_df.set_index('hex_id', inplace=True)

# read target csv
target_df = pd.read_csv('warszawa.csv')
target_df.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
target_df.set_index('hex_id', inplace=True)

h2o.init()
h2o_df = h2o.H2OFrame(main_df)
x = list(main_df.columns)
y = 'OHCA'

aml = H2OAutoML(max_models=20, seed=1, max_runtime_secs=10)
aml.train(x=x, y=y, training_frame=h2o_df)

lb = aml.leaderboard
# save leaderboard to csv
# check if a leader was found
if lb is not None:
    # save leaderboard to csv
    lb_df = lb.as_data_frame()
    lb_df.to_csv('leaderboard.csv')

# Get the best model
leader_model = aml.leader
# save as binary for python
model_path = h2o.save_model(model=leader_model, path=".", force=True)

# Predict and add to target csv
target_df = h2o.H2OFrame(target_df)
predictions = leader_model.predict(target_df)
predictions_df = predictions.as_data_frame()
target_df = target_df.as_data_frame()
target_df['predictions'] = predictions_df
target_df.to_csv('predictions.csv')


# Shutdown h2o
h2o.cluster().shutdown()

