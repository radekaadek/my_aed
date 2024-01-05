import overpass

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

if __name__ == "__main__":
    api = overpass.API()
    a = get_point_data("amenity", "Joniec", overpass.API())
    print(a)
