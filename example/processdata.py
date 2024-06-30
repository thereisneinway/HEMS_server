import numpy as np
import pandas as pd

weekday_mapping = {
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4,
    'Friday': 5,
    'Saturday': 6,
    'Sunday': 7
}

df = pd.read_csv('raw_data.csv')

df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d-%m-%y %H:%M')
df['day'] = df['timestamp'].dt.day_name().map(weekday_mapping)
df.drop(['timestamp'], axis=1, inplace=True)


df['temp_Bedroom temp'] = df['temp_Bedroom temp'].replace(0, np.nan)
df['temp_Outdoor temp'] = df['temp_Outdoor temp'].replace(0, np.nan)

max_temp = df[['temp_Bedroom temp','temp_Outdoor temp']].max().max()
min_temp = df[['temp_Bedroom temp','temp_Outdoor temp']].min().min()


df['temp_Bedroom temp'] = (df['temp_Bedroom temp'] - min_temp)/(max_temp-min_temp)
df['temp_Outdoor temp'] = (df['temp_Outdoor temp'] - min_temp)/(max_temp-min_temp)
df['day'] = (df['day'] -1)/(7-1)





df.to_csv('processed_data.csv', index=False)