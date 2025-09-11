import pandas as pd
from datetime import timedelta, timezone, date, time
import json
import altair as alt
pd.set_option('display.max_rows', 5)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from pandas import Timestamp
import pytz
from etl import whoop,amazfit
import numpy as np
xml_file_path = "data/apple_health_export/export.xml"

def parse_apple_health_xml(xml_file_path):
    """
    Parse Apple Health XML export and return a pandas DataFrame with useful variables.
    """
    if not os.path.exists(xml_file_path):
        raise FileNotFoundError(f"XML file not found: {xml_file_path}")

    data = []

    # Sleep analysis value mapping for better readability
    sleep_value_map = {
        'HKCategoryValueSleepAnalysisInBed': 'In Bed',
        'HKCategoryValueSleepAnalysisAsleep': 'Asleep',
        'HKCategoryValueSleepAnalysisAwake': 'Awake',
        'HKCategoryValueSleepAnalysisAsleepCore': 'Core Sleep',
        'HKCategoryValueSleepAnalysisAsleepDeep': 'Deep Sleep',
        'HKCategoryValueSleepAnalysisAsleepREM': 'REM Sleep'
    }

    # Workout activity type mapping for better readability
    workout_type_map = {
        'HKWorkoutActivityTypeRunning': 'Running',
        'HKWorkoutActivityTypeWalking': 'Walking',
        'HKWorkoutActivityTypeCycling': 'Cycling',
        'HKWorkoutActivityTypeSwimming': 'Swimming',
        'HKWorkoutActivityTypeHiking': 'Hiking',
        'HKWorkoutActivityTypeYoga': 'Yoga',
        'HKWorkoutActivityTypePilates': 'Pilates',
        'HKWorkoutActivityTypeCrossTraining': 'Cross Training',
        'HKWorkoutActivityTypeFunctionalStrengthTraining': 'Strength Training',
        'HKWorkoutActivityTypeTraditionalStrengthTraining': 'Weightlifting',
        'HKWorkoutActivityTypeHighIntensityIntervalTraining': 'HIIT',
        'HKWorkoutActivityTypeDance': 'Dance',
        'HKWorkoutActivityTypeTennis': 'Tennis',
        'HKWorkoutActivityTypeBasketball': 'Basketball',
        'HKWorkoutActivityTypeSoccer': 'Soccer',
        'HKWorkoutActivityTypeOther': 'Other'
    }

    # Use iterparse for memory-efficient parsing of large XML files
    for event, elem in ET.iterparse(xml_file_path, events=('end',)):
        if elem.tag == 'Record':
            record_data = {}

            # Extract key attributes from Record elements
            record_data['type'] = elem.get('type', '')
            record_data['sourceName'] = elem.get('sourceName', '')
            record_data['sourceVersion'] = elem.get('sourceVersion', '')
            record_data['unit'] = elem.get('unit', '')
            record_data['creationDate'] = elem.get('creationDate', '')
            record_data['startDate'] = elem.get('startDate', '')
            record_data['endDate'] = elem.get('endDate', '')
            record_data['value'] = elem.get('value', '')

            # Extract metadata if available
            metadata_entries = elem.findall('MetadataEntry')
            for metadata in metadata_entries:
                key = metadata.get('key', '')
                value = metadata.get('value', '')
                record_data[f'metadata_{key}'] = value

            # Catchall: Extract all other attributes and child elements
            catchall_data = {}

            # Get all attributes not already extracted
            standard_attrs = {'type', 'sourceName', 'sourceVersion', 'unit',
                            'creationDate', 'startDate', 'endDate', 'value'}
            for attr_name, attr_value in elem.attrib.items():
                if attr_name not in standard_attrs:
                    catchall_data[f'attr_{attr_name}'] = attr_value

            # Get all child elements that aren't MetadataEntry
            for child in elem:
                if child.tag != 'MetadataEntry':
                    if child.tag not in catchall_data:
                        catchall_data[child.tag] = []
                    child_data = {'text': child.text, 'attributes': child.attrib}
                    # Get grandchild elements
                    grandchildren = []
                    for grandchild in child:
                        grandchildren.append({
                            'tag': grandchild.tag,
                            'text': grandchild.text,
                            'attributes': grandchild.attrib
                        })
                    if grandchildren:
                        child_data['children'] = grandchildren
                    catchall_data[child.tag].append(child_data)

            # Store catchall data as JSON string if not empty
            if catchall_data:
                import json
                record_data['catchall_json'] = json.dumps(catchall_data, default=str)

            data.append(record_data)

        elif elem.tag == 'Workout':
            # Handle Workout elements
            workout_data = {}

            # Extract workout attributes
            workout_data['type'] = 'HKWorkoutTypeIdentifier'  # Standard workout type identifier
            workout_data['sourceName'] = elem.get('sourceName', '')
            workout_data['sourceVersion'] = elem.get('sourceVersion', '')
            workout_data['unit'] = ''  # Workouts don't have units
            workout_data['creationDate'] = elem.get('creationDate', '')
            workout_data['startDate'] = elem.get('startDate', '')
            workout_data['endDate'] = elem.get('endDate', '')
            workout_data['value'] = ''  # Workouts don't have a single value

            # Extract workout-specific attributes
            workout_type = elem.get('workoutActivityType', '')
            workout_data['workoutActivityType'] = workout_type_map.get(workout_type, workout_type)
            workout_data['duration'] = elem.get('duration', '')
            workout_data['durationUnit'] = elem.get('durationUnit', '')
            workout_data['totalDistance'] = elem.get('totalDistance', '')
            workout_data['totalDistanceUnit'] = elem.get('totalDistanceUnit', '')
            workout_data['totalEnergyBurned'] = elem.get('totalEnergyBurned', '')
            workout_data['totalEnergyBurnedUnit'] = elem.get('totalEnergyBurnedUnit', '')

            # Extract metadata entries
            metadata_entries = elem.findall('MetadataEntry')
            for metadata in metadata_entries:
                key = metadata.get('key', '')
                value = metadata.get('value', '')
                workout_data[f'metadata_{key}'] = value

            # Extract workout events and statistics
            catchall_data = {}

            # Get all attributes not already extracted
            standard_attrs = {'sourceName', 'sourceVersion', 'creationDate', 'startDate', 'endDate',
                            'workoutActivityType', 'duration', 'durationUnit', 'totalDistance',
                            'totalDistanceUnit', 'totalEnergyBurned', 'totalEnergyBurnedUnit'}
            for attr_name, attr_value in elem.attrib.items():
                if attr_name not in standard_attrs:
                    catchall_data[f'attr_{attr_name}'] = attr_value

            # Get all child elements
            for child in elem:
                if child.tag not in catchall_data:
                    catchall_data[child.tag] = []
                child_data = {'text': child.text, 'attributes': child.attrib}

                # Get grandchild elements
                grandchildren = []
                for grandchild in child:
                    grandchildren.append({
                        'tag': grandchild.tag,
                        'text': grandchild.text,
                        'attributes': grandchild.attrib
                    })
                if grandchildren:
                    child_data['children'] = grandchildren
                catchall_data[child.tag].append(child_data)

            # Store catchall data as JSON string if not empty
            if catchall_data:
                import json
                workout_data['catchall_json'] = json.dumps(catchall_data, default=str)

            data.append(workout_data)

            # Clear element to save memory
            elem.clear()

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Convert date columns to datetime
    date_columns = ['creationDate', 'startDate', 'endDate']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Handle different data types appropriately
    # Sleep analysis values should remain as strings
    sleep_mask = df['type'] == 'HKCategoryTypeIdentifierSleepAnalysis'
    df.loc[sleep_mask, 'value'] = df.loc[sleep_mask, 'value'].map(sleep_value_map).fillna(df.loc[sleep_mask, 'value'])

    # Convert other values to numeric where possible
    numeric_mask = ~sleep_mask
    df.loc[numeric_mask, 'value'] = pd.to_numeric(df.loc[numeric_mask, 'value'], errors='coerce')

    # Add duration column for time-based records
    if 'startDate' in df.columns and 'endDate' in df.columns:
        df['duration_minutes'] = (df['endDate'] - df['startDate']).dt.total_seconds() / 60

    return df

# Parse the XML and create DataFrame
try:
    health_df = parse_apple_health_xml(xml_file_path)
    
    print(f"Successfully parsed {len(health_df)} records")
    print(f"Columns: {list(health_df.columns)}")
    print(f"Data types found: {health_df['type'].unique()[:10]}")  # Show first 10 types

    # Display basic info
    print("\nDataFrame Info:")
    print(health_df.info())

    print("\nSample data:")
    print(health_df.head())

    # Show sleep analysis data specifically
    sleep_data = health_df[health_df['type'] == 'HKCategoryTypeIdentifierSleepAnalysis']
    if not sleep_data.empty:
        print(f"\nSleep Analysis Records: {len(sleep_data)}")
        print("Sleep states found:")
        print(sleep_data['value'].value_counts())
        print("\nSample sleep data:")
        print(sleep_data[['startDate', 'endDate', 'value', 'duration_minutes', 'sourceName']].head())

    # Show workout data specifically
    workout_data = health_df[health_df['type'] == 'HKWorkoutTypeIdentifier']
    if not workout_data.empty:
        print(f"\nWorkout Records: {len(workout_data)}")
        print("Workout types found:")
        print(workout_data['workoutActivityType'].value_counts())
        print("\nSample workout data:")
        workout_columns = ['startDate', 'endDate', 'workoutActivityType', 'duration', 'totalDistance', 'totalEnergyBurned', 'sourceName']
        available_columns = [col for col in workout_columns if col in workout_data.columns]
        print(workout_data[available_columns].head())

        # Show workout statistics
        if 'duration' in workout_data.columns:
            workout_data['duration'] = pd.to_numeric(workout_data['duration'], errors='coerce')
            print("\nWorkout duration statistics:")
            print(workout_data['duration'].describe())

        if 'totalEnergyBurned' in workout_data.columns:
            workout_data['totalEnergyBurned'] = pd.to_numeric(workout_data['totalEnergyBurned'], errors='coerce')
            print("\nEnergy burned statistics:")
            print(workout_data['totalEnergyBurned'].describe())

    # Show catchall data info
    catchall_count = health_df['catchall_json'].notna().sum()
    if catchall_count > 0:
        print(f"\nRecords with additional catchall data: {catchall_count}")
        print("Sample catchall data:")
        sample_catchall = health_df[health_df['catchall_json'].notna()].head(1)
        if not sample_catchall.empty:
            print(sample_catchall['catchall_json'].iloc[0][:200] + "..." if len(sample_catchall['catchall_json'].iloc[0]) > 200 else sample_catchall['catchall_json'].iloc[0])

except Exception as e:
    print(f"Error parsing XML: {e}")
    health_df = pd.DataFrame()

##
workout_data
sleep_data
# Ensure the comparison uses the same timezone as 'creationDate'
tz = health_df['startDate'].dt.tz
result_df = health_df[health_df['startDate'] >= pd.to_datetime('23-08-2025', dayfirst=True).tz_localize(tz)]
##
result_df
result_df=result_df.drop_duplicates(['type','sourceName','sourceVersion','unit','creationDate','startDate','endDate','value'],keep='last')

result_df['sourceName'].value_counts(dropna=False)
result_df['type'].value_counts(dropna=False)

result_df['date']=result_df['startDate'].dt.date
result_df['date']=pd.to_datetime(result_df['date'])
result_df['time']=result_df['startDate'].dt.time
result_df['startDate']
##
amazfit_ah=result_df[result_df['sourceName']=='Zepp']
whoop_ah=result_df[result_df['sourceName']=='WHOOP']

amazfit_ah['type'].value_counts(dropna=False)

# whoop
""" HKQuantityTypeIdentifierHeartRate
HKCategoryTypeIdentifierSleepAnalysis
HKQuantityTypeIdentifierRespiratoryRate
HKQuantityTypeIdentifierRestingHeartRate
HKQuantityTypeIdentifierActiveEnergyBurned      

HKQuantityTypeIdentifierOxygenSaturation """


# amazfit
""" HKQuantityTypeIdentifierHeartRate
HKCategoryTypeIdentifierSleepAnalysis
HKQuantityTypeIdentifierRespiratoryRate
HKQuantityTypeIdentifierRestingHeartRate 
HKQuantityTypeIdentifierActiveEnergyBurned

HKQuantityTypeIdentifierStepCount """

##
#region categorization
""" Categorization """
# rhr 
af_resting=amazfit_ah[amazfit_ah['type']=="HKQuantityTypeIdentifierRestingHeartRate"][['sourceName',"creationDate", "startDate", "endDate", "value","duration_minutes",'unit','date','time']]
wh_resting=whoop_ah[whoop_ah['type']=="HKQuantityTypeIdentifierRestingHeartRate"][['sourceName',"creationDate", "startDate", "endDate", "value","duration_minutes",'unit','date','time']]

# hearth
af_hearth=amazfit_ah[amazfit_ah['type']=='HKQuantityTypeIdentifierHeartRate'][['sourceName',"creationDate", "startDate", "endDate", "value","duration_minutes",'unit','date','time']]
wh_hearth=whoop_ah[whoop_ah['type']=='HKQuantityTypeIdentifierHeartRate'][['sourceName',"creationDate", "startDate", "endDate", "value","duration_minutes",'unit','date','time']]

# respiratory
af_resp=amazfit_ah[amazfit_ah['type']=='HKQuantityTypeIdentifierRespiratoryRate'][['sourceName',"creationDate", "startDate", "endDate", "value","duration_minutes",'unit','date','time']]
wh_resp=whoop_ah[whoop_ah['type']=='HKQuantityTypeIdentifierRespiratoryRate'][['sourceName',"creationDate", "startDate", "endDate", "value","duration_minutes",'unit','date','time']]

# sleep
af_sleep=amazfit_ah[amazfit_ah['type']=='HKCategoryTypeIdentifierSleepAnalysis'][['sourceName',"creationDate", "startDate", "endDate", "value","duration_minutes",'unit','date','time']]
wh_sleep=whoop_ah[whoop_ah['type']=='HKCategoryTypeIdentifierSleepAnalysis'][['sourceName',"creationDate", "startDate", "endDate", "value","duration_minutes",'unit','date','time']]

# energy
af_energy=amazfit_ah[amazfit_ah['type']=="HKQuantityTypeIdentifierActiveEnergyBurned"][['sourceName',"creationDate", "startDate", "endDate", "value","duration_minutes",'unit','date','time']]
wh_energy=whoop_ah[whoop_ah['type']=="HKQuantityTypeIdentifierActiveEnergyBurned"][['sourceName',"creationDate", "startDate", "endDate", "value","duration_minutes",'unit','date','time']]

# workout
af_workouts=amazfit_ah[amazfit_ah['type']=="HKWorkoutTypeIdentifier"]
wh_workouts=whoop_ah[whoop_ah['type']=="HKWorkoutTypeIdentifier"]

def selectWorkout(af_workouts,wh_workouts,date='06-09-2025'):    
    # workout del 6 settembre
    af_workout=af_workouts[af_workouts.date==pd.to_datetime(date,dayfirst=True)].reset_index().drop('index', axis=1, errors='ignore')
    wh_workout=wh_workouts[wh_workouts.date==pd.to_datetime(date,dayfirst=True)].reset_index().drop('index', axis=1, errors='ignore')

    af_workout
    af_workout['catchall_json']=af_workout['catchall_json'].apply(lambda x: json.loads(x))
    af_workout=pd.concat([af_workout.reset_index().drop('catchall_json',axis=1),pd.json_normalize(af_workout['catchall_json'])],axis=1)
    af_workout=af_workout[['sourceName',"creationDate", "startDate", "endDate", "workoutActivityType", "duration",'WorkoutStatistics', "date", "time"]]

    wh_workout['catchall_json']=wh_workout['catchall_json'].apply(lambda x: json.loads(x))
    wh_workout=pd.concat([wh_workout.reset_index().drop('catchall_json',axis=1),pd.json_normalize(wh_workout['catchall_json'])],axis=1)
    wh_workout=wh_workout[['sourceName',"creationDate", "startDate", "endDate", "workoutActivityType", "duration",'WorkoutStatistics', "date", "time"]]

    wh_workout.startDate[0]
    wh_workout.endDate[0]

    wh_workout['heart']=[wh_hearth[(wh_hearth.startDate >= wh_workout.startDate.iloc[0]) & (wh_hearth.endDate <= wh_workout.endDate.iloc[0])].to_dict(orient='records')]
    af_workout['heart']=[af_hearth[(af_hearth.startDate >= af_workout.startDate.iloc[0]) & (af_hearth.endDate <= af_workout.endDate.iloc[0])].to_dict(orient='records')]
    return wh_workout, af_workout

# endregion

##
c_timespan_wh = alt.Chart(wh_hearth).mark_line(color='royalblue').encode(
    x=alt.X('startDate:T',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('value:Q',#scale=alt.Scale(zero=False)
    ),
    #color=alt.Color(''),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
).properties(
    width=500,
    height=200,
    
).interactive()
c_timespan_wh
##
c_timespan_af = alt.Chart(af_hearth).mark_line(color='royalblue').encode(
    x=alt.X('startDate:T',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('value:Q',#scale=alt.Scale(zero=False)
    ),
    #color=alt.Color(''),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
).properties(
    width=500,
    height=200,
)
c_timespan_af


##
#region RHR
# RHR
""" apple health """
af_resting
print(af_resting.head(50).to_markdown())

# input manuale di un dato mancante
tzinfo = timezone(timedelta(hours=2))
af_resting.loc[len(af_resting.index)] = [
    'Zepp',
    pd.to_datetime('02-09-2025',dayfirst=True).tz_localize(tz),
    pd.to_datetime('02-09-2025',dayfirst=True).tz_localize(tz),
    pd.to_datetime('02-09-2025',dayfirst=True).tz_localize(tz),
    56.0, 0.0, 'count/min', date(2025, 9, 2), time(0, 0)
]

##
c_rhr_af = alt.Chart(af_resting[['sourceName','startDate','value']]).mark_line(color='royalblue').encode(
    x=alt.X('startDate:T',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('value',scale=alt.Scale(zero=False)
    ),
    color=alt.Color('sourceName'),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
).interactive()
c_rhr_af
c_rhr_wh = alt.Chart(wh_resting[['sourceName','startDate','value']]).mark_line(color='red').encode(
    x=alt.X('startDate:T',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('value',scale=alt.Scale(zero=False)
    ),
    color=alt.Color('sourceName'),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
).interactive()
c_rhr_wh

c_rhr_wh+c_rhr_af
##
#endregion 

#region sleep
# sleep
""" apple health + enrichment con dump whoop """
# whoop in bed sleep awake ma su whoop il dump è diverso

whoop['sleeps']['Cycle start time']=pd.to_datetime(whoop['sleeps']['Cycle start time'])

af_sleep[af_sleep.value=='In Bed']
whoop['sleeps']=whoop['sleeps'][whoop['sleeps']['Cycle start time']>=pd.to_datetime('23-08-2025', dayfirst=True)]
wh_sleep=wh_sleep.reset_index()
# Aggregate duration_minutes by date and value (sum if multiple per day)
wh_sleep_pivot = (
    wh_sleep.groupby(['date', 'value'], dropna=False)['duration_minutes']
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)
whoop['sleeps']['date']=whoop['sleeps']['Cycle start time'].dt.date
whoop['sleeps']['date']=pd.to_datetime(whoop['sleeps']['date'])

wh_sleep_ext=pd.merge(whoop['sleeps'], wh_sleep_pivot, how='left',on='date', )

wh_sleep_ext=wh_sleep_ext[['date',"Sleep onset"	,"Wake onset",'In bed duration (min)', 'Light sleep duration (min)', 'Deep (SWS) duration (min)', 'REM duration (min)', 'Awake duration (min)', ]]

wh_sleep_ext_melt=wh_sleep_ext.melt(id_vars=['date',"Sleep onset"	,"Wake onset"],var_name='sleep_type',value_name='duration_minutes')

wh_sleep_ext_melt.sleep_type.value_counts(dropna=False)
sleepVarMap={
    'In bed duration (min)': "In Bed",
    'Light sleep duration (min)': "Core Sleep",
    'Deep (SWS) duration (min)': "Deep Sleep",
    'REM duration (min)': "REM Sleep" ,
    'Awake duration (min)': "Awake",
}
wh_sleep_ext_melt['value'] = wh_sleep_ext_melt['sleep_type'].map(sleepVarMap)
af_sleep.value.value_counts(dropna=False)
sleep_compare=pd.merge(wh_sleep_ext_melt, af_sleep, how='left',on=['date','value'], suffixes=('_whoop', '_amazfit'), indicator=False)
sleep_compare=sleep_compare.sort_values(by=['date'],ascending=True)
 

##

amazfit_sleep_melt=amazfit['sleep'][["date","deepSleepTime", "shallowSleepTime", "wakeTime", "REMTime"]].melt(id_vars=['date'],var_name='sleep_type',value_name='duration_minutes')

print(amazfit_sleep_melt['sleep_type'].value_counts(dropna=False).head(50).to_markdown())
sleepVarMap1={
    "deepSleepTime"    :"Deep Sleep",
    "shallowSleepTime" :"Core Sleep",
    "wakeTime"         :"Awake",
    "REMTime"          :"REM Sleep",
}
amazfit_sleep_melt['value'] = amazfit_sleep_melt['sleep_type'].map(sleepVarMap1)
amazfit_sleep_melt
wh_sleep_ext_melt['date']
amazfit_sleep_melt['date']=pd.to_datetime(amazfit_sleep_melt['date'])
wh_sleep_ext_melt['date']=pd.to_datetime(wh_sleep_ext_melt['date'])
amazfit_sleep_melt[amazfit_sleep_melt['date']==pd.to_datetime('2025-08-23',dayfirst=True)]
wh_sleep_ext_melt[wh_sleep_ext_melt['date']==pd.to_datetime('2025-08-23',dayfirst=True)]


sleep_compare1=pd.merge(wh_sleep_ext_melt, amazfit_sleep_melt, how='left',on=['date','value'], suffixes=('_whoop', '_amazfit'), indicator=True)
sleep_compare1=sleep_compare1.sort_values(by=['date'],ascending=True)
 
sleep_compare1=sleep_compare1[sleep_compare1['_merge']=='both']

sleep_compare1

##
c_sleep_comp_wh = alt.Chart(sleep_compare1).mark_line(color='royalblue').encode(
    x=alt.X('date:T',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('duration_minutes_whoop:Q',#scale=alt.Scale(zero=False)
    ),
    color=alt.Color('value'),
    # yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
)
c_sleep_comp_af = alt.Chart(sleep_compare1).mark_line(color='royalblue').encode(
    x=alt.X('date:T',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('duration_minutes_amazfit:Q',#scale=alt.Scale(zero=False)
    ),
    color=alt.Color('value'),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
)


c_sleep_comp=c_sleep_comp_af.properties(title=alt.TitleParams(
    ['Amazfit' ]  
),width=300, height=200,) | c_sleep_comp_wh.properties(title=alt.TitleParams(
    ['Whoop' ],
),width=300, height=200,)

c_sleep_comp
##
af_sleep['origValue']=af_sleep['value']
##
sleepVarMap2={
    "In Bed": "In Bed",
    "Awake": "Awake",
    "Core Sleep": "HKCategoryValueSleepAnalysisAsleepUnspecified",
    "Deep Sleep": "HKCategoryValueSleepAnalysisAsleepUnspecified",
    "REM Sleep": "HKCategoryValueSleepAnalysisAsleepUnspecified",
}
af_sleep['value']=af_sleep['origValue'].map(sleepVarMap2)
af_sleep.groupby(['date','value','duration_minutes'],dropna=False).sum()
grouped_per_day_af=af_sleep.groupby(['date','value'],dropna=False)['duration_minutes'].agg([np.sum]).reset_index()
grouped_per_day_wh=wh_sleep.groupby(['date','value'],dropna=False)['duration_minutes'].agg([np.sum]).reset_index()
grouped_per_day_wh['sourceName']='WHOOP'
grouped_per_day_af['sourceName']='Zepp'
##

c_sleepCycle_perDay_wh = alt.Chart(grouped_per_day_wh).mark_line(color='royalblue').encode(
    x=alt.X('date:T',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('sum:Q',#scale=alt.Scale(zero=False)
    ),
    color=alt.Color('value'),
    tooltip=alt.Tooltip('sum:Q'),
    yOffset='sourceName:O'
    
)
c_sleepCycle_perDay_af = alt.Chart(grouped_per_day_af).mark_line(color='royalblue').encode(
    x=alt.X('date:T',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('sum:Q',#scale=alt.Scale(zero=False)
    ),
    color=alt.Color('value'),
    tooltip=alt.Tooltip('sum:Q'),
    yOffset='sourceName:O'
    #facet=alt.Facet('site:O', columns=2),
)


(c_sleepCycle_perDay_wh+ c_sleepCycle_perDay_af).properties(
    width=500,
    height=200,
).interactive()
##
##
# più granulare
c_sleepInBed_af = alt.Chart(af_sleep[af_sleep['value'].isin(['In Bed','Awake'])][['sourceName','startDate','value','duration_minutes']]).mark_line(color='royalblue').encode(
    x=alt.X('startDate',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('duration_minutes',#scale=alt.Scale(zero=False)
    ),
    color=alt.Color('value'),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
).properties(
    title=alt.TitleParams(
    ['Amazfit' ]  ),
    width=300,
    height=200,
)
c_sleepInBed_wh = alt.Chart(wh_sleep[wh_sleep['value'].isin(['In Bed','Awake'])][['sourceName','startDate','value','duration_minutes']]).mark_line(color='royalblue').encode(
    x=alt.X('startDate',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('duration_minutes',#scale=alt.Scale(zero=False)
    ),
    color=alt.Color('value'),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
).properties(
    title=alt.TitleParams(
    ['Whoop' ]  
),
    width=300,
    height=200,
)
c_sleepInBed=c_sleepInBed_wh | c_sleepInBed_af
##

#endregion 

#region hrv
# HRV
""" exported data whoop + integrazione a mano per amazfit --> export amazfit pessimo """
whoop['physiological_cycles']['Cycle start time']=pd.to_datetime(whoop['physiological_cycles']['Cycle start time'])
whoop['physiological_cycles']=whoop['physiological_cycles'][whoop['physiological_cycles']['Cycle start time']>=pd.to_datetime('23-08-2025', dayfirst=True)]


whoop['physiological_cycles']['date']=pd.to_datetime(whoop['physiological_cycles']['Wake onset']).dt.date
whoop['physiological_cycles']=whoop['physiological_cycles'].sort_values(by='date',ascending=True)
whoop['physiological_cycles']['date'].tolist()
whoop['physiological_cycles']['date']=pd.to_datetime(whoop['physiological_cycles']['date'])

# imputo manualmente la serie HRV di amazfit perchè non la esporta in nessun modo
from io import StringIO
csvString = """
date,value
23-08-2025,53
24-08-2025,44
25-08-2025,46
26-08-2025,61
27-08-2025,57
28-08-2025,42
29-08-2025,47
30-08-2025,53
31-08-2025,43
01-09-2025,54
02-09-2025,51
03-09-2025,62
04-09-2025,57
05-09-2025,57
"""

csvStringIO = StringIO(csvString)
amazfitHRV = pd.read_csv(csvStringIO, sep=",")
amazfitHRV['date']=pd.to_datetime(amazfitHRV['date'],dayfirst=True)

whoopHRV=whoop['physiological_cycles'][['date','Heart rate variability (ms)']]
whoopHRV['sourceName']='WHOOP'
amazfitHRV['sourceName']='Zepp'
##
c_hrv_wh = alt.Chart(whoopHRV).mark_line(color='red').encode(
    x=alt.X('date',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('Heart rate variability (ms)',scale=alt.Scale(zero=False)
    ),
    color=alt.Color('sourceName'),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
)
c_hrv_af = alt.Chart(amazfitHRV).mark_line(color='royalblue').encode(
    x=alt.X('date',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('value',scale=alt.Scale(zero=False)
    ),
    color=alt.Color('sourceName'),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
)
c_hrv_af+c_hrv_wh
##
#endregion 

#region tasso respiratorio
# tasso respiratorio
""" apple health """
# af esporta al minuto wh esporta giornaliero

test=af_resp[af_resp['date']==pd.to_datetime('23-08-2025',dayfirst=True)]

averaged_af_resp=af_resp.groupby(['date'],dropna=False)['value'].agg([np.mean,np.median,np.std,np.sum,np.size]).reset_index()
averaged_af_resp['sourceName']='Zepp'
##
c_resp_wh = alt.Chart(wh_resp.drop('time',axis=1)).mark_line(color='red').encode(
    x=alt.X('date:T',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('value',scale=alt.Scale(zero=False)
    ),
    color=alt.Color('sourceName'),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
)
c_resp_af = alt.Chart(averaged_af_resp).mark_line(color='royalblue').encode(
    x=alt.X('date:T',#sort='y',bin=alt.Bin(maxbins=5)
    ),
    y=alt.Y('mean',scale=alt.Scale(zero=False)
    ),
    color=alt.Color('sourceName'),
    #yOffset='variable'
    #facet=alt.Facet('site:O', columns=2),
)

c_resp_af+c_resp_wh
##
# endregion

#region workouts
# compare workouts
""" apple health: manuale """
# hearth rate dove matcha durante workout
""" apple health """
# whoop logga solo durante le attività fisiche più volte al minuto
wh_hearth
# amazfit logga sempre ogni 1 minuto + workout
af_hearth
af_workouts.date.unique()

def plotWorkout(wh_workout,af_workout):
    wh_hearth_workout=pd.DataFrame(wh_workout['heart'][0])
    len(wh_hearth_workout['value'])
    wh_hearth_workout['value'].mean()
    wh_hearth_workout['value'].min()
    wh_hearth_workout['value'].max()

    af_hearth_workout=pd.DataFrame(af_workout['heart'][0])
    len(af_hearth_workout['value'])
    af_hearth_workout['value'].mean()
    af_hearth_workout['value'].min()
    af_hearth_workout['value'].max()
    ##
    hr_compare={
        "whoop":{
            "tipo":wh_workout['workoutActivityType'].iloc[0],
            "durata":round(float(wh_workout['duration'].iloc[0]),1),
            'lunghezza serie battiti':len(wh_hearth_workout['value']),
            'media battiti':round(wh_hearth_workout['value'].mean(),1),
            'min battiti':wh_hearth_workout['value'].min(),
            'max battiti':wh_hearth_workout['value'].max(),
            "energia bruciata":wh_workout['WorkoutStatistics'][0][0]['attributes']['sum'] +' cal',
            
        },
        "amazfit":{
            'tipo': 'Strength Training (manuale)' if af_workout['workoutActivityType'].iloc[0]=='Strength Training' else af_workout['workoutActivityType'].iloc[0],
            'durata':round(float(af_workout['duration'].iloc[0]),1),
            'lunghezza serie battiti':len(af_hearth_workout['value']),
            'media battiti':round(af_hearth_workout['value'].mean(),1),
            'min battiti':af_hearth_workout['value'].min(),
            'max battiti':af_hearth_workout['value'].max(),
            'energia bruciata':af_workout['WorkoutStatistics'][0][0]['attributes']['sum'] +' cal',
            
        }
    }

    hr_compare=pd.DataFrame(hr_compare)
    hr_compare
    ##
    ##


    af_hearth_workout.iloc[0].time
    wh_hearth_workout_comp=wh_hearth_workout[wh_hearth_workout.time>=af_hearth_workout.iloc[0].time]
    wh_hearth_workout_comp.iloc[-1].time
    af_hearth_workout_comp=af_hearth_workout[af_hearth_workout.time<=wh_hearth_workout_comp.iloc[-1].time]

    ##
    c_heart_wh = alt.Chart(wh_hearth_workout_comp.drop(['time','date'],axis=1)).mark_line(color='red').encode(
        x=alt.X('startDate:T',#sort='y',bin=alt.Bin(maxbins=5)
        ),
        y=alt.Y('value',scale=alt.Scale(zero=False)
        ),
        color=alt.Color('sourceName'),
        #yOffset='variable'
        #facet=alt.Facet('site:O', columns=2),
    )
    c_heart_af = alt.Chart(af_hearth_workout_comp.drop('time',axis=1)).mark_line(color='royalblue').encode(
        x=alt.X('startDate:T',#sort='y',bin=alt.Bin(maxbins=5)
        ),
        y=alt.Y('value',scale=alt.Scale(zero=False)
        ),
        color=alt.Color('sourceName'),
        #yOffset='variable'
        #facet=alt.Facet('site:O', columns=2),
    )
    c_heart=c_heart_wh+c_heart_af
    return hr_compare,c_heart
##

wh_workout,af_workout=selectWorkout(af_workouts,wh_workouts,date='06-09-2025')
hr_compare_0609,c_heart_0609=plotWorkout(wh_workout,af_workout)

wh_workout,af_workout=selectWorkout(af_workouts,wh_workouts,date='03-09-2025')
hr_compare_0309,c_heart_0309=plotWorkout(wh_workout,af_workout)

wh_workout,af_workout=selectWorkout(af_workouts,wh_workouts,date='30-08-2025')
hr_compare_3008,c_heart_3008=plotWorkout(wh_workout,af_workout)

#endregion


