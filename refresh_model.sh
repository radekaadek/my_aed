#!/bin/bash
SECONDS_IN_MINUTE=60
MINUTES_IN_HOUR=60
HOURS_IN_DAY=24
DAYS_IN_WEEK=7
SECONDS_IN_DAY=$((SECONDS_IN_MINUTE * MINUTES_IN_HOUR * HOURS_IN_DAY))
while true; do
    python3 aquire_data.py
    python3 create_main_df.py
    python3 train_model.py
    python3 make_predictions.py
    sleep $((SECONDS_IN_DAY))
done

