from OSMPythonTools.overpass import Overpass, overpassQueryBuilder
from OSMPythonTools.nominatim import Nominatim
import requests
import pandas as pd
import h3
import shapely
import pyproj
import numpy as np
import time

def get_point_data(node_name: str, area_name: str, date: str = None) -> list[dict]:
    """Get point data from Overpass API in the form of a list of dictionaries:

    geometry: (lat, lon), type: node_name

    Keyword arguments:

    node_name -- name of the node to get data from
    area_name -- name of the area to get data from
    api -- overpass API object
    """
    
    # query = ""
    # if date is not None: # to jeszcze nie dziala :(
    #     query += f'[date:"{date}"];'
    # else:
    #     query += ''
    # query += f'''
    # area["name"="{area_name}"]->.a;
    # (
    #     node["{node_name}"](area.a);
    # );
    # out center;
    # '''
    if date is None:
        # set to current date
        date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # ovapi = Overpass()
    nomatim = Nominatim()
    areaid = nomatim.query(area_name).areaId()
    query = overpassQueryBuilder(area=areaid, elementType='node', selector=node_name, out='center', includeGeometry=True)
    query = '[out:json][timeout:900];' + query
    print(f"Query: {query}")
    # r = ovapi.query(query, date=date, timeout=900)
    base_url = "https://overpass-api.de/api/interpreter"
    # body is query
    r = requests.post(base_url, data=query, timeout=900)
    # print(r.text)
    resp = r.json()
    nodes = []
    for node in resp['elements']:
        node_geom = (node["lat"], node["lon"])
        name = node["tags"][node_name]
        nodes.append({"geometry": node_geom, "type": name})
    return nodes


def get_building_data(area_name: str, date: str = None) -> pd.DataFrame:
    """Get building data from Overpass API in the form of a pandas DataFrame:

    Building name, Geometry

    Keyword arguments:

    area_name -- name of the area to get data from
    api -- overpass API object
    date -- date of the data (default None)
    """
    # query = f"""
    # [out:json][timeout:900];
    # area["name"="{area_name}"]->.a;
    # (
    #     way["building"](area.a);
    #     relation["building"](area.a);
    # );
    # out body;
    # >;
    # out geom;
    # """
    if date is None:
        # set to current date
        date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ovapi = Overpass()
    nomatim = Nominatim()
    areaid = nomatim.query(area_name).areaId()
    query = overpassQueryBuilder(area=areaid, elementType=['way', 'relation'], selector='building', out='body geom')
    query = '[out:json][timeout:900];' + query
    print(f"Query: {query}")
    # r = ovapi.query(query, date=date, timeout=900)
    base_url = "https://overpass-api.de/api/interpreter"
    # body is query
    req = requests.post(base_url, data=query, timeout=900)
    r = req.json()
    buildings = []
    for building in r['elements']:
        if 'geometry' in building.keys():
            geometry = building['geometry']
        else:
            continue
        if 'tags' in building.keys():
            if 'amenity' in building['tags'].keys():
                name = building['tags']['amenity']
            elif 'building' in building['tags'].keys():
                name = building['tags']['building']
            else:
                name = 'unknown'
        else:
            name = 'unknown'
        buildings.append({"name": name, "geometry": geometry})
    retv = pd.DataFrame(buildings)
    return retv

def get_feature_df(area_name: str, date: str = None, hexagon_res: int = 9) -> pd.DataFrame:
    """Get feature data from Overpass API in the form of a DataFrame with one column 'name' and of which
    values are teh number of features of that type in the area. The index is the hexagon id.

    Keyword arguments:

    area_name -- name of the area to get data from
    api -- overpass API object
    date -- date of the data (default None)
    """
    if date is None:
        # set to current date
        date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    node_names = ['amenity', 'building', 'highway', 'public_transport',
                  'government', 'leisure', 'office', 'emergency', 'natural',
                  'advertising'] #natural not used emergency
    amenities = get_point_data(node_names[0], area_name, date=date)
    highways = get_point_data(node_names[2], area_name, date=date)
    public_transport = get_point_data(node_names[3], area_name, date=date)
    government = get_point_data(node_names[4], area_name, date=date)
    leisure = get_point_data(node_names[5], area_name, date=date)
    office = get_point_data(node_names[6], area_name, date=date)
    emergency = get_point_data(node_names[7], area_name, date=date)
    advertising = get_point_data(node_names[9], area_name, date=date)
    pt_list = []
    pt_list.extend(amenities)
    pt_list.extend(highways)
    pt_list.extend(leisure)
    pt_list.extend(office)
    pt_list.extend(government)
    pt_list.extend(public_transport)
    pt_list.extend(emergency)
    pt_list.extend(advertising)
    # create a dataframe
    retv = pd.DataFrame(columns=['hex_id', 'name'])
    for amenity in amenities:
        hex_id = h3.latlng_to_cell(amenity['geometry'][0], amenity['geometry'][1], hexagon_res)
        retv.loc[len(retv)] = {'hex_id': hex_id, 'name': amenity['type']}
    retv = retv.groupby(['hex_id', 'name']).size()
    retv = retv.reset_index()
    # pivot the table
    retv = retv.pivot(index='hex_id', columns='name', values=0)
    # fill NaNs with 0
    retv = retv.fillna(0)
    return retv

def get_area_df(building_df: pd.DataFrame, hexagon_res: int = 9) -> pd.DataFrame:
    """Calculate area of buildings for hexagon grid, return a GeoDataFrame:

    Feature 1 name, Feature 2 name,
    Feature 1 area in m^2, Feature 2 area in m^2,

    Indexed by hexagon id.

    Keyword arguments:

    building_gdf -- GeoDataFrame with building data
    hexagon_res -- resolution of the hexagon grid (default 9)
    """
    # input df:
    #                 name  geometry
    # 0                yes  [{'lat': 51.9247658, 'lon': 18.1166587}, {'lat...
    # 1            library  [{'lat': 51.9163144, 'lon': 18.1129191}, {'lat...
    # 2                yes  [{'lat': 51.91845, 'lon': 18.1099972}, {'lat':...
    # 3    public_building  [{'lat': 51.9185897, 'lon': 18.1121521}, {'lat...
    inproj = pyproj.Proj('EPSG:4326')
    outproj = pyproj.Proj('EPSG:9835')
    transformer = pyproj.Transformer.from_proj(inproj, outproj)
    # get hexagons which intersect with buildings
    # columns are unique building names
    # rows are hexagon ids
    rows_to_add = []
    for i, row in building_df.iterrows():
        print(f"Processing row {i} of {len(building_df)}")
        # get latlons of the building
        latlons = [(point['lat'], point['lon']) for point in row['geometry']]
        # delete last point if it is the same as the first one
        if len(latlons) > 1 and latlons[0] == latlons[-1]:
            latlons.pop()
        # convert to h3 polygon
        p = h3.Polygon(latlons)
        # p to a shapely polygon
        ppoly = shapely.geometry.Polygon(latlons)
        hexagons = h3.polygon_to_cells(p, hexagon_res)
        # this only returns cells fully contained in the polygon
        # add cells on the border
        for lat, lon in latlons:
            hexagons.add(h3.latlng_to_cell(lat, lon, hexagon_res))
        # make the list unique
        hexagons = set(hexagons)
        # calculate area of intersection
        for hexagon in hexagons:
            hexagon_polygon = h3.cell_to_boundary(hexagon)
            hexagon_polygon = [transformer.transform(point[0], point[1]) for point in hexagon_polygon]
            hexagon_polygon = shapely.geometry.Polygon(hexagon_polygon)
            intersection = hexagon_polygon.intersection(ppoly)
            area = intersection.area
            rows_to_add.append({'hex_id': hexagon, 'name': row['name'], 'area': area})
    
    retv = pd.DataFrame(rows_to_add, columns=['hex_id', 'name', 'area'])
    retv = retv.groupby(['hex_id', 'name']).sum()
    retv = retv.reset_index()
    # pivot the table
    retv = retv.pivot(index='hex_id', columns='name', values='area')
    retv = retv.reset_index()
    # fill NaNs with 0
    retv = retv.fillna(0)
    return retv


def add_neighbours(df: pd.DataFrame) -> pd.DataFrame:
    """Takes in a dataframe with hex_id as index and adds columns with neighbour counts.

    Keyword arguments:

    df -- dataframe with hex_id as index
    """
    # create a neighbour column for each column in df
    retv = df.copy()
    retv = pd.concat([retv, pd.DataFrame(columns=[f'{col}_neighbour_count' for col in retv.columns])])
    integer_columns = [col for col in retv.columns if retv[col].dtype == 'int64']
    # get neighbours of each hexagon
    processed = 0
    for hex_id in df.index:
        print(f"Processing hexagon {processed} of {len(df)}")
        processed += 1
        neighbours = h3.grid_disk(hex_id, 1)
        # get only neighbours that are in df
        neighbours_in_df = [neighbour for neighbour in neighbours if neighbour in df.index]
        for col in df.columns:
            col_name = f'{col}_neighbour_count'
            # add value of hex_id to neighbours
            retv.loc[neighbours_in_df, col_name] += df.at[hex_id, col]
            # convert back to int if necessary
            if col in integer_columns:
                retv[col_name] = retv[col_name].astype(int)
    # fill NaNs with 0
    retv = retv.fillna(0)
    return retv

def get_all_data(area_name: str, hexagon_res: int = 9, get_neighbours: bool = True, date: str = None) -> pd.DataFrame:
    # combine data from get_feature_df and get_area_df
    feature_df = get_feature_df(area_name, date=date, hexagon_res=hexagon_res)
    building_df = get_building_data(area_name, date=date)
    print(building_df)
    s = time.time()
    area_df = get_area_df(building_df, hexagon_res)
    e = time.time()
    print(f"Time to get area data: {e-s}")
    # merge the two dataframes
    retv = pd.merge(feature_df, area_df, on='hex_id', how='outer')
    # set index to hex_id
    retv = retv.set_index('hex_id')
    # fill NaNs with 0
    retv = retv.fillna(0)
    # convert all data to float32
    retv = retv.astype(np.float32)
    # sum data from neighbours and add to dataframe as {feature}_neighbour_count
    if get_neighbours:
        s = time.time()
        retv = add_neighbours(retv)
        e = time.time()
        print(f"Time to add neighbours: {e-s}")
    return retv
if __name__ == "__main__":

    # a = get_building_data("Montgomery County", api)
    # save to csv
    # a.to_csv('montgomery_building.csv', index=False)
    # a = get_all_data("Montgomery County", date="2018-06-01T00:00:00Z")
    # a.to_csv('montgomery_county_osm.csv')
    # test
    # b = get_all_data("Lublin")
    # b.to_csv('lublin_osm.csv')
    d = get_all_data("Montgomery County", date="2018-06-01T00:00:00Z")
    d.to_csv('montgomery_osm.csv')
    c = get_all_data("Cincinnati, Ohio", date="2018-06-01T00:00:00Z")
    c.to_csv('cincinnati_osm.csv')
    
    # test getting ammenities from get_point_data
    # amenities = get_point_data("amenity", "Virginia Beach", api)
    # print(amenities)
    # test getting buildings from get_building_data
    # buildings = get_point_data("building", "Virginia Beach", api)
    # print(buildings)