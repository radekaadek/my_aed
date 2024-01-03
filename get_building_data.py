import overpass
import json

def get_data(area_name):
    query = f"""
    area["name"="{area_name}"]->.a;
    (
        way["building"](area.a);
        relation["building"](area.a);
    );
    out body;
    >;
    out skel qt;
    """
    api = overpass.API()
    respu = None
    try:
        respu = api.get(query, responseformat="json")
    except Exception as e:
        print(f"An error a: {e}")
        respu = None
    return respu

with open('data.json', 'w') as outfile:
    json.dump(get_data('Warszawa'), outfile)

