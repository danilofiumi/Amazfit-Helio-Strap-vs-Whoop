import pandas as pd
import os
pd.set_option('display.max_rows', 5)
libname=os.path.dirname(os.path.abspath(__file__))
os.chdir(libname) if os.path.exists(libname) else print(f'{libname} not found')
del libname

# whoop
wh_e_journal_entries = pd.read_csv("data/my_whoop_data_2025_09_05/journal_entries.csv")
wh_e_physiological_cycles = pd.read_csv("data/my_whoop_data_2025_09_05/physiological_cycles.csv")
wh_e_sleeps = pd.read_csv("data/my_whoop_data_2025_09_05/sleeps.csv")
wh_e_workouts = pd.read_csv("data/my_whoop_data_2025_09_05/workouts.csv")

whoop={
    'journal_entries':wh_e_journal_entries,
    'physiological_cycles':wh_e_physiological_cycles,
    'sleeps':wh_e_sleeps,
    'workouts':wh_e_workouts
}

# path_list=[]
# for root, dirs, files in os.walk("data/7083440919_1757061409163"):
#     for file in files:
#         if file.endswith(".csv"):
#              path_list.append(root+"/" +file)

#amazfit
af_e_sleep=pd.read_csv('data/7083440919_1757061409163/SLEEP/SLEEP_1757061408677.csv')
af_e_activity=pd.read_csv('data/7083440919_1757061409163/ACTIVITY/ACTIVITY_1757061408622.csv')
af_e_body=pd.read_csv('data/7083440919_1757061409163/BODY/BODY_1757061408764.csv')
af_e_sport=pd.read_csv('data/7083440919_1757061409163/SPORT/SPORT_1757061408780.csv')
af_e_user=pd.read_csv('data/7083440919_1757061409163/USER/USER_1757061408603.csv')
af_e_heartrate_auto=pd.read_csv('data/7083440919_1757061409163/HEARTRATE_AUTO/HEARTRATE_AUTO_1757061408754.csv')
af_e_health_data=pd.read_csv('data/7083440919_1757061409163/HEALTH_DATA/HEALTH_DATA_1757061408588.csv')
af_e_activity_stage=pd.read_csv('data/7083440919_1757061409163/ACTIVITY_STAGE/ACTIVITY_STAGE_1757061408633.csv')
af_e_activity_minute=pd.read_csv('data/7083440919_1757061409163/ACTIVITY_MINUTE/ACTIVITY_MINUTE_1757061408649.csv')
af_e_heartrate=pd.read_csv('data/7083440919_1757061409163/HEARTRATE/HEARTRATE_1757061408690.csv')

amazfit={
    'sleep':af_e_sleep,
    'activity':af_e_activity,
    'body':af_e_body,
    'sport':af_e_sport,
    'user':af_e_user,
    'heartrate_auto':af_e_heartrate_auto,
    'health_data':af_e_health_data,
    'activity_stage':af_e_activity_stage,
    'activity_minute':af_e_activity_minute,
    'heartrate':af_e_heartrate
}


whoop['journal_entries']
whoop['physiological_cycles']
whoop['sleeps']
whoop['workouts']



