import numpy as np
import pandas as pd
from sklearn.cluster import FeatureAgglomeration
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier

target = 'predictions'

# NOTE: Make sure that the outcome column is labeled 'target' in the data file
tpot_data = pd.read_csv('main_hexagon_df.csv')
tpot_data.rename(columns={'Unnamed: 0': 'hex_id'}, inplace=True)
tpot_data.set_index('hex_id', inplace=True)
features = tpot_data.drop(target, axis=1)
training_features, testing_features, training_target, testing_target = \
            train_test_split(features, tpot_data[target], random_state=None)

# Average CV score on the training set was: 0.8183131812142985
exported_pipeline = make_pipeline(
    FeatureAgglomeration(affinity="l2", linkage="complete"),
    DecisionTreeClassifier(criterion="entropy", max_depth=2, min_samples_leaf=3, min_samples_split=10)
)

exported_pipeline.fit(training_features, training_target)
results = exported_pipeline.predict(testing_features)
# add to main df and save as predictions.csv
testing_features[target] = results
testing_features.to_csv('predictions.csv')
