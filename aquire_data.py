from OSMPythonTools.overpass import overpassQueryBuilder
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
    # create a dictionary
    data_for_df = {'hex_id': [], 'name': [], 'length': []}
    for line in line_data:
        hexes = {h3.latlng_to_cell(point['lat'], point['lon'], 9) for point in line['geometry']}
        for hexagon in hexes:
            length = line_hexagon_length([(point['lat'], point['lon']) for point in line['geometry']], hexagon)
            data_for_df['hex_id'].append(hexagon)
            data_for_df['name'].append(line['type'])
            data_for_df['length'].append(length)
    # transpose the dictionary
    retv = pd.DataFrame(data_for_df)
    # set index to hex_id
    # transpose the DataFrame
    retv = retv.pivot_table(index='hex_id', columns='name', values='length', aggfunc='sum', fill_value=0)
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

inproj = pyproj.Proj('EPSG:4326')
outproj = pyproj.Proj('EPSG:3857')
transformer = pyproj.Transformer.from_proj(inproj, outproj)
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
    # transform
    x, y = transformer.transform(x, y)
    # transform line to EPSG:3857
    lats = [point[0] for point in line]
    lons = [point[1] for point in line]
    line_x, line_y = transformer.transform(lats, lons)
    # create a polygon
    hex_bpoly = shapely.geometry.Polygon(zip(x, y))
    # create a line
    line = shapely.geometry.LineString(zip(line_x, line_y))
    # get intersection
    intersection = hex_bpoly.intersection(line)
    # get length
    length = intersection.length
    return length


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
        try:
            transformed_geometry.append(shapely.geometry.Polygon(zip(x, y)))
        except Exception as e: # life is life
            transformed_geometry.append(shapely.geometry.Polygon())
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
    retv = df
    basic_cols = retv.columns
    # add columns for neighbours
    for col in basic_cols:
        retv[f'{col}_neighbour_count'] = np.float32(0)
    # add columns to retv
    
    # iterate over all neighbours for each hexagon and add its values to neighbours neighbour_count columns
    for hexagon in retv.index:
        neighbours = h3.grid_disk(hexagon, 1)
        for neighbour in neighbours:
            if neighbour in retv.index and neighbour != hexagon:
                for col in basic_cols:
                    retv.loc[neighbour, f'{col}_neighbour_count'] += retv.loc[hexagon, col]
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
    # add prefix area_ to area_df columns, dont change hex_id
    building_area_df.columns = [f"area_{col}" if col != 'hex_id' else col for col in building_area_df.columns]
    landuse_area_df.columns = [f"area_{col}" if col != 'hex_id' else col for col in landuse_area_df.columns]
    leisure_area_df.columns = [f"area_{col}" if col != 'hex_id' else col for col in leisure_area_df.columns]
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
    # if get_neighbours:
    #     s = time.time()
    #     retv = add_neighbours(retv)
    #     e = time.time()
    #     print(f"Time to add neighbours: {e-s}")
    return retv


if __name__ == "__main__":
    a = get_all_data("Montgomery County, PA", date="2018-06-01T00:00:00Z")
    c = get_all_data("Cincinnati, Ohio", date="2018-06-01T00:00:00Z")
    d = get_all_data("Virginia Beach", date="2018-06-01T00:00:00Z")
    final = pd.concat([a, c, d], axis=0, ignore_index=False)
    # fill NaNs with 0s
    final = final.fillna(0)
    # drop row with all 0s
    final = final[(final.T != 0).any()]
    final.to_csv('osm_data.csv')
    target = get_all_data("Warszawa")
    target = target.fillna(0)
    target = target[(target.T != 0).any()]
    target.to_csv('warszawa_osm.csv')

