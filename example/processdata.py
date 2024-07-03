import numpy as np
import pandas as pd

weekday_mapping = {
    'Monday': 1,
    'Tuesday': 1,
    'Wednesday': 1,
    'Thursday': 1,
    'Friday': 1,
    'Saturday': 0,
    'Sunday': 0
}
dfs = pd.read_csv('raw_data_16days.csv')
dfs['timestamp'] = pd.to_datetime(dfs['timestamp'], format='%d-%m-%y %H:%M')
dfs['weekday'] = dfs['timestamp'].dt.day_name().map(weekday_mapping)
dfs.set_index('timestamp', inplace=True)
df = dfs[dfs.index.minute % 10 == 0].copy()

#df.drop(['timestamp'], axis=1, inplace=True)
print(df)


df['temp_Bedroom temp'] = df['temp_Bedroom temp'].replace(0, np.nan)
df['temp_Outdoor temp'] = df['temp_Outdoor temp'].replace(0, np.nan)
df['light_environment'] = df['light_environment'].replace(0, np.nan)

max_temp = df[['temp_Bedroom temp','temp_Outdoor temp']].max().max()
min_temp = df[['temp_Bedroom temp','temp_Outdoor temp']].min().min()


df['temp_Bedroom temp'] = (df['temp_Bedroom temp'] - min_temp)/(max_temp-min_temp)
df['temp_Outdoor temp'] = (df['temp_Outdoor temp'] - min_temp)/(max_temp-min_temp)
df['light_environment'] = (df['light_environment'] - 1)/(3-1)





#df.to_csv('processed_data.csv', index=True)