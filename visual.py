# draw the map
import requests
import pandas as pd
import h3

poland_df = pd.read_csv('predictions.csv')

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

max_ohca = poland_df['OHCA'].max()

# get top 10 hexagons with the most predicted ohca that have no defibrillators or hospitals
top_10_hexagons = poland_df[poland_df['aed_count'] == 0].sort_values(by='OHCA', ascending=False).head(10)

# add hexagons with opacity based on the number of ohca
for i, row in poland_df.iterrows():
    if row['aed_count'] == 0 and row['hospital_x'] == 0:
        boundary = h3.cell_to_boundary(i)
        if row['OHCA'] >= top_10_hexagons['OHCA'].min():
            folium.Polygon(locations=boundary, fill_color='blue', fill_opacity=row['OHCA']/max_ohca/2).add_to(m)
        else:
            folium.Polygon(locations=boundary, fill_color='red', fill_opacity=row['OHCA']/max_ohca/2).add_to(m)

    else:
        boundary = h3.cell_to_boundary(i)
        folium.Polygon(locations=boundary, fill_color='green', fill_opacity=row['OHCA']/max_ohca/2).add_to(m)
m.save('warsaw.html')