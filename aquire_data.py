import overpass
import pandas as pd
import geopandas as gpd
import h3
import shapely
import pyproj
import numpy as np
import time

def get_point_data(node_name: str, area_name: str, api: overpass.API, date: str = None) -> list[dict]:
    """Get point data from Overpass API in the form of a list of dictionaries:

    geometry: (lat, lon), type: node_name

    Keyword arguments:

    node_name -- name of the node to get data from
    area_name -- name of the area to get data from
    api -- overpass API object
    """
    
    query = ""
    # if date is not None: # to jeszcze nie dziala :(
    #     query += f'[date:"{date}"];'
    # else:
    #     query += ''
    query += f'''
    area["name"="{area_name}"]->.a;
    (
        node["{node_name}"](area.a);
    );
    out center;
    '''
    resp = api.get(query)
    nodes = []
    for node in resp['features']:
        node_geom = node["geometry"]["coordinates"]
        name = node["properties"][node_name]
        nodes.append({"geometry": node_geom, "type": name})
    return nodes


def get_building_data(area_name: str, api: overpass.API, date: str = None) -> pd.DataFrame:
    """Get building data from Overpass API in the form of a pandas DataFrame:

    Building name, Geometry

    Keyword arguments:

    area_name -- name of the area to get data from
    api -- overpass API object
    date -- date of the data (default None)
    """
    query = f"""
    area["name"="{area_name}"]->.a;
    (
        way["building"](area.a);
        relation["building"](area.a);
    );
    out body;
    >;
    out geom;
    """
    r = api.get(query, responseformat="json")
    # example response:
    # name, nodes, geometry
    # create a dataframe just with name and nodes
    buildings = []
    if 'elements' not in r:
        raise Exception("No elements in response")
    for building in r['elements']:
        if 'tags' in building and 'building' in building['tags'] and 'nodes' in building:
            buildings.append({"name": building['tags']['building'], "nodes": building['nodes']})
    # create a dict {node_id: (lat, lon)}
    node_to_latlon = {}
    for node in r['elements']:
        if 'type' in node and node['type'] == 'node' and 'id' in node and 'lat' in node and 'lon' in node:
            node_to_latlon[node['id']] = (node['lat'], node['lon'])
    # create the dataframe
    buildings_df = pd.DataFrame(data=buildings)
    # create a column with lat and lon
    for i, row in buildings_df.iterrows():
        latlons = []
        for node_id in row['nodes']:
            latlons.append(node_to_latlon[node_id])
        buildings_df.at[i, 'geometry'] = shapely.geometry.Polygon(latlons)
    # drop the nodes column
    buildings_df = buildings_df.drop(columns=['nodes'])
    # create a GeoDataFrame
    buildings_gdf = gpd.GeoDataFrame(buildings_df, geometry='geometry', crs='EPSG:4326')
    return buildings_gdf

def get_feature_df(area_name: str, api: overpass.API, date: str = None, hexagon_res: int = 9) -> pd.DataFrame:
    """Get feature data from Overpass API in the form of a DataFrame with one column 'name' and of which
    values are teh number of features of that type in the area. The index is the hexagon id.

    Keyword arguments:

    area_name -- name of the area to get data from
    api -- overpass API object
    date -- date of the data (default None)
    """
    
    node_names = ['amenity', 'building', 'highway', 'public_transport', 'government', 'leisure', 'office', 'emergency', 'natural'] #natural not used emergency
    amenities = get_point_data(node_names[0], area_name, api)
    highways = get_point_data(node_names[2], area_name, api)
    public_transport = get_point_data(node_names[3], area_name, api)
    government = get_point_data(node_names[4], area_name, api)
    leisure = get_point_data(node_names[5], area_name, api)
    office = get_point_data(node_names[6], area_name, api)
    emergency = get_point_data(node_names[7], area_name, api)
    pt_list = []
    pt_list.extend(amenities)
    pt_list.extend(highways)
    pt_list.extend(leisure)
    pt_list.extend(office)
    pt_list.extend(government)
    pt_list.extend(public_transport)
    pt_list.extend(emergency)
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
    inproj = pyproj.Proj('EPSG:4326')
    outproj = pyproj.Proj('EPSG:9835')
    transformer = pyproj.Transformer.from_proj(inproj, outproj)
    # get hexagons which intersect with buildings
    # columns are unique building names
    # rows are hexagon ids
    rows_to_add = []
    for i, row in building_df.iterrows():
        print(f"Processing row {i} of {len(building_df)}")
        latlons = [(lat, lon) for lat, lon in row['geometry'].exterior.coords]
        # delete last point if it is the same as the first one
        if len(latlons) > 1 and latlons[0] == latlons[-1]:
            latlons.pop()
        # convert to h3 polygon
        p = h3.Polygon(latlons)
        hexagons = h3.polygon_to_cells(p, hexagon_res)
        # this only returns cells fully contained in the polygon
        # add cells on the border
        for lat, lon in latlons:
            hexagons.add(h3.latlng_to_cell(lat, lon, hexagon_res))
        # make the list unique
        hexagons = set(hexagons)
        # calculate area of intersection
        for hexagon in hexagons:
            # calculate intersection using shapely
            bdry = shapely.geometry.Polygon(h3.cell_to_boundary(hexagon, False))
            row_xy = shapely.geometry.Polygon(row['geometry'])
            # convert to xy coordinates using pyproj
            bdry = shapely.ops.transform(transformer.transform, bdry)
            row_xy = shapely.ops.transform(transformer.transform, row_xy)
            # convert to shapely polygon
            bdry = shapely.geometry.Polygon(bdry)
            inter_area = bdry.intersection(row_xy).area
            # add to dataframe
            # dict_to_add = {'hex_id': hexagon, 'name': row['name'], 'area': inter_area}
            rows_to_add.append((hexagon, row['name'], inter_area))
    
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

def get_all_data(area_name: str, api: overpass.API, hexagon_res: int = 9, get_neighbours: bool = True) -> pd.DataFrame:
    # combine data from get_feature_df and get_area_df
    feature_df = get_feature_df(area_name, api, hexagon_res=hexagon_res)
    building_df = get_building_data(area_name, api)
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
    api = overpass.API()

    # a = get_all_data("Marin County", api)
    # a.to_csv("marin.csv")

    b = get_point_data("amenity", "Marin County", api)
    print(b)
    # test getting ammenities from get_point_data
    # amenities = get_point_data("amenity", "Virginia Beach", api)
    # print(amenities)
    # test getting buildings from get_building_data
    # buildings = get_point_data("building", "Virginia Beach", api)
    # print(buildings)