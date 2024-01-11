import pandas as pd
import h2o
from h2o.automl import H2OAutoML

target = 'OHCA'
# Read the defata
main_df = pd.read_csv('main_hexagon_df.csv')

print(main_df.head())

# shuffle rows
main_df = main_df.sample(frac=1)

h2o.init(max_mem_size='60G')
# drop the unnamed column
main_df = main_df.drop(['Unnamed: 0'], axis=1)
h2o_df = h2o.H2OFrame(main_df)
x = list(main_df.columns)
y = target

# Exclude this
excluded_algos = ["StackedEnsemble"]

aml = H2OAutoML(seed=1, max_runtime_secs=3600, exclude_algos=excluded_algos)
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
