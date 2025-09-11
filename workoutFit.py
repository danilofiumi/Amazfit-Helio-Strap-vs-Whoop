from fitparse import FitFile
import pandas as pd

# Replace 'yourfile.fit' with your actual file path
fitfile = FitFile('data/Zepp20250906193128.fit')

records = []
for record in fitfile.get_messages('record'):
    data = {}
    for field in record:
        data[field.name] = field.value
    records.append(data)

workout_fit = pd.DataFrame(records)


workout_fit


import pandas as pd
import xml.etree.ElementTree as ET

tree = ET.parse('data/Zepp20250903204118.tcx')
root = tree.getroot()

# TCX files use namespaces, so we need to handle them
ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}

records = []
for activity in root.findall('.//tcx:Activity', ns):
    for lap in activity.findall('tcx:Lap', ns):
        for track in lap.findall('tcx:Track', ns):
            for trackpoint in track.findall('tcx:Trackpoint', ns):
                data = {}
                time = trackpoint.find('tcx:Time', ns)
                position = trackpoint.find('tcx:Position', ns)
                altitude = trackpoint.find('tcx:AltitudeMeters', ns)
                distance = trackpoint.find('tcx:DistanceMeters', ns)
                hr = trackpoint.find('.//tcx:HeartRateBpm/tcx:Value', ns)
                cadence = trackpoint.find('tcx:Cadence', ns)

                if time is not None:
                    data['time'] = time.text
                if position is not None:
                    lat = position.find('tcx:LatitudeDegrees', ns)
                    lon = position.find('tcx:LongitudeDegrees', ns)
                    if lat is not None:
                        data['latitude'] = lat.text
                    if lon is not None:
                        data['longitude'] = lon.text
                if altitude is not None:
                    data['altitude'] = altitude.text
                if distance is not None:
                    data['distance'] = distance.text
                if hr is not None:
                    data['heart_rate'] = hr.text
                if cadence is not None:
                    data['cadence'] = cadence.text

                records.append(data)

workout_tcx = pd.DataFrame(records)

workout_tcx
workout_fit

 