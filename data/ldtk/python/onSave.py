# Runs after saving

# Read world.ldtk as json
# For each level in the levels array, save it to its own json file

import os
import json
import shutil

# Read world.ldtk
root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
path = os.path.join(root, 'world.ldtk')
data = json.loads(open(path, 'r').read())

# Create export folder
exportFolder = os.path.join(root, "data")
os.makedirs(exportFolder, exist_ok=True)

# Copy each level to its own json file
# Also create index file for keeping track of level iids
index = {}
for level in data['levels']:
    f = open(os.path.join(exportFolder, level['identifier']+".json"), 'w') #+"_"+level['iid']
    index[level['iid']] = {}
    index[level['iid']]['identifier'] = level['identifier']
    index[level['iid']]['worldX'] = level['worldX']
    index[level['iid']]['worldY'] = level['worldY']
    json.dump(level, f)
    f.close()

i = open(os.path.join(exportFolder, "index.json"), 'w')
json.dump(index, i)
i.close()