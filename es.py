# print the first 1000 characters of warsaw_buildings.json
# dont load the whole file into memory

# read as a text file
with open('virginia_buildings.json', 'r') as f:
    data = f.read()
    print(data[:1000])