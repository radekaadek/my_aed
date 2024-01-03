import overpass

q = 
way(95777558);
out geom;
"""
api = overpass.API()
r = api.get(q)
print(r)
