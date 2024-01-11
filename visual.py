# draw the map
import numpy as np
import requests
import pandas as pd
import h3

target = 'OHCA'
poland_df = pd.read_csv('predictions.csv')
# delete the first row
# print the last 5 rows
print(poland_df.tail())

aed_url = 'https://aed.openstreetmap.org.pl/aed_poland.geojson'
aed_file = requests.get(aed_url)
aed_json = aed_file.json()
# create a column with aed count

poland_df['aed_count'] = 0

# iterate through aeds find the hexagon and add 1 to the column
for aed in aed_json['features']:
    x, y = aed["geometry"]["coordinates"]
    hexagon = h3.latlng_to_cell(y, x, 9)
    if hexagon in poland_df.index:
        poland_df.loc[hexagon, 'aed_count'] += 1
# create a map, color hexagons by the predicted number of ohca
import folium

m = folium.Map(location=[52.2297, 21.0122], zoom_start=11)

max_ohca = np.round(poland_df[target].max())

# get top 10 hexagons with the most predicted ohca that have no defibrillators or hospitals
top_10_hexagons = poland_df[poland_df['aed_count'] == 0].sort_values(by=target, ascending=False).head(10)

# add hexagons with opacity based on the number of ohca
for _, row in poland_df.iterrows():
    i = row['hex_id']
    try:
        locations = h3.cell_to_boundary(i)
    except: # i am too tired of this
        continue
    fill_value = row[target] / max_ohca
    if row['aed_count'] == 0:
        # if its in top 10 hexagons make it blue
        if i in top_10_hexagons.index:
            folium.Polygon(
                locations=locations,
                color='blue',
                fill_color='blue',
                fill_opacity=fill_value,
                popup='Predicted OHCA: {}'.format(row[target])
            ).add_to(m)
        else:
            folium.Polygon(
                locations=locations,
                color='red',
                fill_color='red',
                fill_opacity=fill_value,
                popup='Predicted OHCA: {}'.format(row[target])
            ).add_to(m)
    else:
        folium.Polygon(
            locations=locations,
            color='green',
            fill_color='green',
            fill_opacity=fill_value,
            popup='Predicted OHCA: {}'.format(row[target])
        ).add_to(m)
m.save('warsaw.html')
