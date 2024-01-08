import pandas as pd
import h2o
from h2o.automl import H2OAutoML

target = 'lvl2'

# Read the defata
main_df = pd.read_csv('main_hexagon_df.csv')

main_df.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
main_df.set_index('hex_id', inplace=True)

# read target csv
target_df = pd.read_csv('warszawa_osm.csv')
target_df.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
target_df.set_index('hex_id', inplace=True)

# drop columns that are not in target_df
target_cols = list(target_df.columns)
for col in main_df.columns:
    if col not in target_cols and col != target:
        main_df.drop(col, axis=1, inplace=True)

# shuffle rows
main_df = main_df.sample(frac=1)

h2o.init()
h2o_df = h2o.H2OFrame(main_df)
x = list(main_df.columns)
y = target

aml = H2OAutoML(seed=1, max_runtime_secs=14400)
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


# Shutdown h2o
h2o.cluster().shutdown()

