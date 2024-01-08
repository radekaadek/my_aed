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
                  'advertising', 'craft', 'sport', 'tourism'] #natural not used emergency
    amenities = get_point_data(node_names[0], area_name, date=date)
    highways = get_point_data(node_names[2], area_name, date=date)
    public_transport = get_point_data(node_names[3], area_name, date=date)
    government = get_point_data(node_names[4], area_name, date=date)
    leisure = get_point_data(node_names[5], area_name, date=date)
    office = get_point_data(node_names[6], area_name, date=date)
    emergency = get_point_data(node_names[7], area_name, date=date)
    advertising = get_point_data(node_names[9], area_name, date=date)
    craft = get_point_data(node_names[10], area_name, date=date)
    sport = get_point_data(node_names[11], area_name, date=date)
    tourism = get_point_data(node_names[12], area_name, date=date)
    pt_list = []
    pt_list.extend(amenities)
    pt_list.extend(highways)
    pt_list.extend(leisure)
    pt_list.extend(office)
    pt_list.extend(government)
    pt_list.extend(public_transport)
    pt_list.extend(emergency)
    pt_list.extend(advertising)
    pt_list.extend(craft)
    pt_list.extend(sport)
    pt_list.extend(tourism)
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

def cells_to_polygon(cells: set[str], hexagon_res: int = 9) -> shapely.geometry.Polygon:
    """Converts a set of cells to a polygon.

    Keyword arguments:

    cells -- set of cells
    hexagon_res -- resolution of the hexagon grid (default 9)
    """
    # convert to a list of tuples
    h3_input = []
    for cell in cells:
        h3_input.extend(h3.cell_to_boundary(cell))
    # get their convex hull
    h3_input = shapely.geometry.MultiPoint(h3_input).convex_hull
    # swap lat and lon in resulting geojsons
    # convert to a shapely polygon
    retv = shapely.geometry.Polygon(h3_input)
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
    outproj = pyproj.Proj('EPSG:3857')
    transformer = pyproj.Transformer.from_proj(inproj, outproj)
    # add a column with converted geometry
    transformed_geometry = []
    for geom in building_df['geometry']:
        lats = [point['lat'] for point in geom]
        lons = [point['lon'] for point in geom]
        x, y = transformer.transform(lats, lons)
        transformed_geometry.append(shapely.geometry.Polygon(zip(x, y)))
    building_df['geometry2'] = transformed_geometry
    rows_to_add = []
    for _, row in building_df.iterrows():
        # get hexagons
        # convert to a list of tuples
        h3_input = [(point['lat'], point['lon']) for point in row['geometry']]
        # get all cells that are in the polygon
        h3_cells = {h3.latlng_to_cell(*point, hexagon_res) for point in h3_input}
        h3_poly = h3.Polygon(h3_input)
        # add cells fully inside
        h3_cells.update(h3.polygon_to_cells(h3_poly, hexagon_res))
        # convert to a bounding polygon
        hex_bpoly_4326 = cells_to_polygon(h3_cells, hexagon_res)
        # transform to EPSG:3857
        # get polygon coords
        x, y = hex_bpoly_4326.exterior.coords.xy
        # transform
        x, y = transformer.transform(x, y)
        # create a polygon
        hex_bpoly = shapely.geometry.Polygon(zip(x, y))
        # get area of the intersection
        intersection = hex_bpoly.intersection(row['geometry2'])
        area = intersection.area
        # add to rows_to_add
        for hex_id in h3_cells:
            rows_to_add.append({'hex_id': hex_id, 'name': row['name'], 'area': area})

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
    # fill them with 0s
    retv = retv.fillna(np.float64(0))
    integer_columns = [col for col in retv.columns if retv[col].dtype == 'int64']
    # get neighbours of each hexagon
    processed = 0
    df_len = len(df)
    for hex_id in df.index:
        print(f"Processing hexagon {processed} of {df_len}")
        processed += 1
        neighbours = h3.grid_disk(hex_id, 1)
        # get neighbours that are only in df
        neighbours_in_df = [neighbour for neighbour in neighbours if neighbour in df.index]
        for col in df.columns:
            col_name = f'{col}_neighbour_count'
            # add value of hex_id to neighbours
            n_val = np.float64(retv.loc[hex_id, col])
            for neighbour_col in neighbours_in_df:
                retv.loc[neighbour_col, col_name] += n_val
    # fill NaNs with 0
    retv = retv.fillna(0)
    return retv

def get_all_data(area_name: str, hexagon_res: int = 9, get_neighbours: bool = True, date: str = None) -> pd.DataFrame:
    # combine data from get_feature_df and get_area_df
    feature_df = get_feature_df(area_name, date=date, hexagon_res=hexagon_res)
    building_df = get_building_data(area_name, date=date)
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
    # a = get_all_data("Montgomery County", date="2018-06-01T00:00:00Z")
    # a.to_csv('montgomery_osm.csv')
    # c = get_all_data("Cincinnati, Ohio", date="2018-06-01T00:00:00Z")
    # c.to_csv('cincinnati_osm.csv')
    # d = get_all_data("Virginia Beach", date="2018-06-01T00:00:00Z")
    # d.to_csv('virginia_beach_osm.csv')
    # target = get_all_data("Warszawa")
    # target.to_csv('warszawa_osm.csv')
    # test get all data
    sochocin = get_all_data("Płońsk", hexagon_res=9)
    sochocin.to_csv('plonsk_osm.csv')
    pass