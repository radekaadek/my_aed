import pandas as pd

target = 'OHCA'
# Read the defata
main_df = pd.read_csv('main_hexagon_df.csv')

# shuffle rows
main_df = main_df.sample(frac=1)
print(main_df.head())
# from tpot import TPOTRegressor
# from sklearn.model_selection import train_test_split
#
# # split into train and test
# X = main_df.drop(target, axis=1)
# y = main_df[target]
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
#
# # train tpot
# tpot = TPOTRegressor(verbosity=2, n_jobs=-1, config_dict='TPOT light')
# tpot.fit(X_train, y_train)
#
# # save tpot model
# tpot.export('tpot_pipeline.py')
#
# # make predictions
# predictions = tpot.predict(X_test)
#
# # print accuracy
# print(tpot.score(X_test, y_test))

import h2o
from h2o.automl import H2OAutoML

h2o.init(max_mem_size='4G')
h2o_df = h2o.H2OFrame(main_df)
x = list(main_df.columns)
y = target

aml = H2OAutoML(seed=1, max_runtime_secs=3600)
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

# from tpot import TPOTRegressor

# # split into train and test
# train = main_df.sample(frac=0.8)
# train_rows = list(train.index)
# test = main_df.drop(train_rows)

# # split into x and y
# train_x = train.drop(target, axis=1)
# train_y = train[target]
# test_x = test.drop(target, axis=1)
# test_y = test[target]

# # train tpot
# tpot = TPOTRegressor(verbosity=2, n_jobs=-1, config_dict='TPOT light')
# tpot.fit(train_x, train_y)

# # save tpot model
# tpot.export('tpot_pipeline.py')

# # make predictions
# predictions = tpot.predict(test_x)

# # print accuracy
# print(tpot.score(test_x, test_y))

# drop 20% of the least correlated columns
# corr_matrix = main_df.corr()
# corr_matrix = corr_matrix[target]
# corr_matrix = corr_matrix.sort_values(ascending=True)
# corr_matrix = corr_matrix[:int(len(corr_matrix) * 0.3)]
# corr_matrix = list(corr_matrix.index)
# main_df.drop(corr_matrix, axis=1, inplace=True)
#
#
# # drop columns that have values > 0 in only 5 rows
# print(f"Cols before dropping columns: {len(main_df.columns)}")
#
# for col in main_df.columns:
#     count = 0
#     for row in main_df[col]:
#         if row > 0:
#             count += 1
#     if count < 5:
#         main_df.drop(col, axis=1, inplace=True)
#
# print(f"Cols after dropping columns: {len(main_df.columns)}")
#
# # train a bunch of models and display their rmse
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import mean_squared_error
# from xgboost import XGBRegressor
# from sklearn.ensemble import RandomForestRegressor
# from sklearn.linear_model import LinearRegression
# from sklearn.svm import SVR
# from sklearn.linear_model import Ridge
# from sklearn.linear_model import Lasso
# from sklearn.linear_model import ElasticNet
# from sklearn.tree import DecisionTreeRegressor
#
# X = main_df.drop(target, axis=1)
# y = main_df[target]
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
#
# models = [XGBRegressor(), RandomForestRegressor(), LinearRegression(), SVR(), Lasso(), ElasticNet(), DecisionTreeRegressor()]
#
# for model in models:
#     model.fit(X_train, y_train)
#     predictions = model.predict(X_test)
#     rmse = mean_squared_error(y_test, predictions, squared=False)
#     print(f"{model.__class__.__name__}: {rmse}")
