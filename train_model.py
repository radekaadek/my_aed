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

aml = H2OAutoML(max_models=20, seed=1, max_runtime_secs=3600)
aml.train(x=x, y=y, training_frame=h2o_df)

lb = aml.leaderboard
# save leaderboard to csv
# check if a leader was found
if lb is not None:
    # save leaderboard
    lb_df = lb.as_data_frame()
    lb_df.to_csv('leaderboard.csv')
    # save leader model
    leader_model = aml.leader
    leader_model.save_mojo('leader_model')
    # save leader model params
    leader_model_params = leader_model.params
    leader_model_params.to_csv('leader_model_params.csv')
else:
    print('No leader model found')
    raise Exception('No leader model found')

# Predict
h2o_target_df = h2o.H2OFrame(target_df)
pred = leader_model.predict(h2o_target_df)
pred_df = pred.as_data_frame()
pred_df.to_csv('pred.csv')

# Shutdown h2o
h2o.cluster().shutdown()

