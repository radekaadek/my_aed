from OSMPythonTools.overpass import overpassQueryBuilder
from OSMPythonTools.nominatim import Nominatim
import requests
import pandas as pd
import h3
import shapely
import pyproj
import numpy as np
import time

logfile = 'log.txt'


def get_point_data(node_name: str, area_name: str, date: str = None) -> list[dict]:
    """Get point data from Overpass API in the form of a list of dictionaries:

    geometry: (lat, lon), type: node_name

    Keyword arguments:

    node_name -- name of the node to get data from
    area_name -- name of the area to get data from
    date -- date of the data (default None)
    """
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
        # print(node)
        node_geom = (node["lat"], node["lon"])
        name = node["tags"][node_name]
        nodes.append({"geometry": node_geom, "type": name})
    return nodes

def get_line_data(node_name: str, area_name: str, date: str = None) -> list[dict]:
    """Get line data from Overpass API in the form of a list of dictionaries:

    geometry: [(lat, lon), (lat, lon), ...], type: node_name

    Keyword arguments:

    node_name -- name of the node to get data from
    area_name -- name of the area to get data from
    date -- date of the data (default None)
    """
    if date is None:
        # set to current date
        date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # ovapi = Overpass()
    nomatim = Nominatim()
    areaid = nomatim.query(area_name).areaId()
    query = overpassQueryBuilder(area=areaid, elementType='way', selector=node_name, out='body geom')
    query = '[out:json][timeout:900];' + query
    print(f"Query: {query}")
    # r = ovapi.query(query, date=date, timeout=900)
    base_url = "https://overpass-api.de/api/interpreter"
    # body is query
    r = requests.post(base_url, data=query, timeout=900)
    # save to file for debugging
    resp = r.json()
    # save to file for debugging
    ways = []
    for way in resp['elements']:
        el = {"geometry": way["geometry"], "type": way["tags"][node_name]}
        ways.append(el)
    return ways

def get_line_df(line_data: list[dict]) -> pd.DataFrame:
    """Convert line data to a DataFrame with columns:

    name, sum of line lengths

    Indexed by hexagon id.

    Keyword arguments:

    line_data -- list of dictionaries with line data
    """
    # input data:
    # [{'geometry': [{'lat': 50.2417639, 'lon': 20.723122}, {'lat': 50.2417077, 'lon': 20.7231886}, {'lat': 50.2411756, 'lon': 20.7238183}], 'type': 'highway'}, {'geometry': [{'lat': 50.24042, 'lon': 20.7183544}, {'lat': 50.2404546, 'lon': 20.718521}, {'lat': 50.2404714, 'lon': 20.718619}, {'lat': 50.2405076, 'lon': 20.7188718}, {'lat': 50.2406439, 'lon': 20.7200494}, {'lat': 50.2406854, 'lon': 20.720379}, {'lat': 50.2407154, 'lon': 20.7205757}, {'lat': 50.2407444, 'lon': 20.720717}, {'lat': 50.240808, 'lon': 20.7209736}, {'lat': 50.2408799, 'lon': 20.7211982}, {'lat': 50.2410184, 'lon': 20.7215398}, {'lat': 50.2413235, 'lon': 20.722232}, {'lat': 50.2415226, 'lon': 20.7226517}, {'lat': 50.2416862, 'lon': 20.7229742}, {'lat': 50.2417639, 'lon': 20.723122}], 'type': 'highway'}, {'geometry': [{'lat': 50.2425086, 'lon': 20.7258192}, {'lat': 50.2430309, 'lon': 20.7258879}, {'lat': 50.2430919, 'lon': 20.7258524}],
    # create a dictionary
    retv = {}
    for line in line_data:
        hexes = set()
        for point in line['geometry']:
            hexes.add(h3.latlng_to_cell(point['lat'], point['lon'], 9))
        for hexagon in hexes:
            h3_input = [(point['lat'], point['lon']) for point in line['geometry']]
            len = line_hexagon_length(h3_input, hexagon)
            name = line['type']
            if hexagon in retv.keys():
                if name in retv[hexagon].keys():
                    retv[hexagon][name] += len
                else:
                    retv[hexagon][name] = len
            else:
                retv[hexagon] = {name: len}

    # convert the dictionary to a dataframe
    retv = pd.DataFrame(retv).T
    # set index Name
    retv.index.name = 'hex_id'
    # fill NaNs with 0s
    retv = retv.fillna(0)
    return retv
    

def get_area_data(area_name: str, selector: str = 'building', tags_to_look_for: list[str] = ['amenity', 'building'], date: str = None) -> pd.DataFrame:
    """Get area data from Overpass API in the form of a pandas DataFrame:

    Name, Geometry

    Keyword arguments:

    area_name -- name of the area to get data from
    date -- date of the data (default None)
    """
    if date is None:
        # set to current date
        date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    nomatim = Nominatim()
    areaid = nomatim.query(area_name).areaId()
    query = overpassQueryBuilder(area=areaid, elementType=['way', 'relation'], selector=selector, out='body geom')
    query = '[out:json][timeout:900];' + query
    print(f"Query: {query}")
    # r = ovapi.query(query, date=date, timeout=900)
    base_url = "https://overpass-api.de/api/interpreter"
    # body is query
    req = requests.post(base_url, data=query, timeout=900)
    r = req.json()
    areas = []
    for area in r['elements']:
        if 'geometry' in area.keys():
            geometry = area['geometry']
        else:
            continue
        if 'tags' in area.keys():
            for tag in tags_to_look_for:
                if tag in area['tags'].keys():
                    name = area['tags'][tag]
                    break
            else:
                name = 'unknown'
        else:
            name = 'unknown'
        areas.append({"name": name, "geometry": geometry})
    retv = pd.DataFrame(areas)
    return retv

def get_feature_df(area_name: str, date: str = None, hexagon_res: int = 9) -> pd.DataFrame:
    """Get feature data from Overpass API in the form of a DataFrame with one column 'name' and of which
    values are the number of features of that type in the area. The index is the hexagon id.

    Keyword arguments:

    area_name -- name of the area to get data from
    date -- date of the data (default None)
    hexagon_res -- resolution of the hexagon grid (default 9)
    """
    if date is None:
        # set to current date
        date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    node_names = ['amenity', 'highway', 'public_transport', 'government', 'leisure', 
                  'office', 'emergency', 'advertising', 'craft', 'sport', 'tourism']

    pt_list = []
    for node in node_names:
        pt_list.extend(get_point_data(node, area_name, date=date))

    # create a dictionary
    data = {'hex_id': [], 'name': []}
    for point in pt_list:
        hex_id = h3.latlng_to_cell(point['geometry'][0], point['geometry'][1], hexagon_res)
        data['hex_id'].append(hex_id)
        data['name'].append(point['type'])

    # convert the dictionary to a DataFrame
    retv = pd.DataFrame(data)

    retv = retv.groupby(['hex_id', 'name']).size().reset_index().pivot(index='hex_id', columns='name', values=0).fillna(0)

    return retv

def cells_to_polygon(cells: set[str]) -> shapely.geometry.Polygon:
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

def line_hexagon_length(line: list[tuple[float, float]], hexagon: str) -> float:
    """Calculate the length of a line that is inside a hexagon.

    Keyword arguments:

    line -- list of tuples (lat, lon)
    hexagon -- hexagon id
    """
    # get the intersection of the line and the hexagon
    # convert to a list of tuples
    hex_bpoly_4326 = cells_to_polygon({hexagon})
    # get polygon coords
    x, y = hex_bpoly_4326.exterior.coords.xy
    # create a polygon
    try:
        hex_bpoly = shapely.geometry.Polygon(zip(x, y))
    except Exception as e:
        # append to log file
        with open(logfile, 'a') as f:
            f.write(f"\nError: \n{e}\n")
        return e
    # get area of the intersection
    intersection = hex_bpoly.intersection(shapely.geometry.LineString(line))
    return intersection.length

# def get_line_df(line_df: pd.DataFrame, hexagon_res: int = 9) -> pd.DataFrame:


def get_area_df(building_df: pd.DataFrame, hexagon_res: int = 9) -> pd.DataFrame:
    """Calculate area of buildings for hexagon grid, return a GeoDataFrame:

    Feature 1 name, Feature 2 name,
    Feature 1 area in m^2, Feature 2 area in m^2,

    Indexed by hexagon id.

    Keyword arguments:

    building_df -- DataFrame with building data
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
        try:
            # get hexagons
            # convert to a list of tuples
            h3_input = [(point['lat'], point['lon']) for point in row['geometry']]
            # get all cells that are in the polygon
            h3_cells = {h3.latlng_to_cell(*point, hexagon_res) for point in h3_input}
            h3_poly = h3.Polygon(h3_input)
            # add cells fully inside
            h3_cells.update(h3.polygon_to_cells(h3_poly, hexagon_res))
            # convert to a bounding polygon
            hex_bpoly_4326 = cells_to_polygon(h3_cells)
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
        except Exception as e:
            print(e)
            continue # yuck i know

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
    retv = retv.fillna(np.float32(0))
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
            n_val = np.float32(retv.loc[hex_id, col])
            for neighbour_col in neighbours_in_df:
                retv.loc[neighbour_col, col_name] += n_val
    # fill NaNs with 0
    retv = retv.fillna(0)
    return retv

def get_all_data(area_name: str, hexagon_res: int = 9, get_neighbours: bool = True, date: str = None) -> pd.DataFrame:
    # combine data from get_feature_df and get_area_df
    feature_df = get_feature_df(area_name, date=date, hexagon_res=hexagon_res)
    building_df = get_area_data(area_name, selector='building', tags_to_look_for=['amenity', 'building'], date=date)
    landuse_df = get_area_data(area_name, selector='landuse', tags_to_look_for=['landuse'], date=date)
    leisure_df = get_area_data(area_name, selector='leisure', tags_to_look_for=['leisure'], date=date)

    line_data = get_line_data('highway', area_name, date=date)
    line_df = get_line_df(line_data)

    s = time.time()
    building_area_df = get_area_df(building_df, hexagon_res)
    landuse_area_df = get_area_df(landuse_df, hexagon_res)
    leisure_area_df = get_area_df(leisure_df, hexagon_res)
    e = time.time()
    print(f"Time to get area data: {e-s}")
    # merge the dfs
    retv = pd.merge(feature_df, building_area_df, on='hex_id', how='outer')
    retv = pd.merge(retv, landuse_area_df, on='hex_id', how='outer')
    retv = pd.merge(retv, leisure_area_df, on='hex_id', how='outer')
    retv = pd.merge(retv, line_df, on='hex_id', how='outer')
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
    try:
        with open(logfile, 'r') as f:
            pass
    except FileNotFoundError:
        # create the file
        with open(logfile, 'w') as f:
            pass
    a = get_all_data("Montgomery County, PA", date="2018-06-01T00:00:00Z")
    a.to_csv('montgomery_osm.csv')
    c = get_all_data("Cincinnati, Ohio", date="2018-06-01T00:00:00Z")
    c.to_csv('cincinnati_osm.csv')
    d = get_all_data("Virginia Beach", date="2018-06-01T00:00:00Z")
    d.to_csv('virginia_beach_osm.csv')
    target = get_all_data("Warszawa")
    target.to_csv('warszawa_osm.csv')
    # test get all data
    pass
