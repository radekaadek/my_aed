import matplotlib.pyplot as plt

# Znajdz najlepsze miejsce na postawienie defibrylatora AED w Warszawie na podstawie danych o lokalizacji defibrylatorow i galerii handlowych
# Znajdziemy najwieksze galerie odlegle od defibrylatorow o dist metrow lub wiecej
dist = 500

# w pliku PL.PZGiK.330.1465__OT_KUHU_A.xml znajduja sie dane o obiektach handlowych w Warszawie
# dane sa w formacie GML, wiec trzeba je przekonwertowac do GeoJSON
# uzyjemy do tego ogr2ogr
# instalacja ogr2ogr: sudo apt install gdal-bin

# import os
# os.system('ogr2ogr -f GeoJSON -t_srs crs:84 galerie.json PL.PZGiK.330.1465__OT_KUHU_A.xml')

# wczytaj dane z pliku galerie.json
import geopandas as gpd
galerie = gpd.read_file('galerie.json')

# w pliku aed_poland.geojson znajduja sie dane o lokalizacji defibrylatorow w Warszawie

# wczytaj dane z pliku aed_poland.geojson
aed = gpd.read_file('aed_poland.geojson')

# wybierz z danych o defibrylatorach te, ktore znajduja sie w Warszawie
warsaw_bounds = (20.85, 52.05, 21.25, 52.35)
aed_warsaw = aed.cx[warsaw_bounds[0]:warsaw_bounds[2], warsaw_bounds[1]:warsaw_bounds[3]]

# wybierz z danych o galeriach handlowych te, ktore znajduja sie w Warszawie
galerie_warsaw = galerie.cx[warsaw_bounds[0]:warsaw_bounds[2], warsaw_bounds[1]:warsaw_bounds[3]]

# policz powierzchnie w m^2 kazdej galerii, uzyj crs
galerie_warsaw['area'] = galerie_warsaw.to_crs(epsg=2180).area

# pokaz galerie odlegle od defibrylatorow o dist m lub wiekszej odleglosci
# uzyj crs
# zachowaj stara geometrie defibrylatorow
aed_warsaw['geometry_old'] = aed_warsaw['geometry']
aed_warsaw = aed_warsaw.to_crs(epsg=2180)
# zachowaj stara geometrie galerii
galerie_warsaw['geometry_old'] = galerie_warsaw['geometry']
galerie_warsaw = galerie_warsaw.to_crs(epsg=2180)
aed_warsaw['geometry'] = aed_warsaw.buffer(dist)
galerie_warsaw['geometry'] = galerie_warsaw.buffer(dist)
galerie_warsaw = galerie_warsaw[~galerie_warsaw.intersects(aed_warsaw.unary_union)]

# policz odleglosci od najblizszych defibrylatorow
# uzyj crs
aed_warsaw = aed_warsaw.to_crs(epsg=2180)
galerie_warsaw = galerie_warsaw.to_crs(epsg=2180)

# Now calculate the distance
galerie_warsaw['distance'] = galerie_warsaw.distance(aed_warsaw.unary_union)


# wybierz galerie, ktore sa odlegle od defibrylatorow o dist m lub wiecej
galerie_warsaw = galerie_warsaw[galerie_warsaw['distance'] > dist]

# wybierz 10 galerii o najwiekszej powierzchni
galerie_warsaw = galerie_warsaw.sort_values(by='area', ascending=False).head(10)


# pokaz na mapie galerie i defibrylatory
import folium
m = folium.Map(location=[52.2297, 21.0122], zoom_start=11)

# zamien crs na 4326
galerie_warsaw = galerie_warsaw.to_crs(epsg=4326)
aed_warsaw = aed_warsaw.to_crs(epsg=4326)

# dodaj galerie uzywajac geometry_old
for i, row in galerie_warsaw.iterrows():
    geom = row['geometry_old']
    folium.GeoJson(geom, style_function=lambda x: {'color': 'blue'}).add_to(m)
    # dodaj czerwony znacznik w srodku galerii
    folium.Marker([geom.centroid.y, geom.centroid.x], icon=folium.Icon(color='red')).add_to(m)

# zapisz mape do pliku
m.save('map.html')