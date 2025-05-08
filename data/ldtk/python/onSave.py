import os
import json
import shutil

# Read world.ldtk
root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
path = os.path.join(root, 'world.ldtk')
data = json.loads(open(path, 'r').read())
grid_size = data["defaultGridSize"]

# Create export folder
exportFolder = os.path.join(root, "data")
os.makedirs(exportFolder, exist_ok=True)

# Copy relevant data to separate JSON files
for level in data['levels']:
    f = open(os.path.join(exportFolder, level['identifier']+".json"), 'w')
    id = level['identifier']
    level_data = {}
    level_data["id"] = id
    level_data["x"] = level['worldX'] // grid_size
    level_data["y"] = level['worldY'] // grid_size
    level_data["width"] = level["pxWid"] // grid_size
    level_data["height"] = level["pxHei"] // grid_size
    level_data["collision"] = level["layerInstances"][0]["intGridCsv"]
    level_data["colors"] = level["layerInstances"][1]["intGridCsv"]
    level_data["field_instances"] = []
    for field in level["fieldInstances"]:
        fi = {}
        fi["id"] = field["__identifier"]
        fi["value"] = field["__value"]
        level_data["field_instances"].append(fi)
    
    level_data["tiles"] = []
    for tile in level["layerInstances"][2]["gridTiles"]:
        t = {}
        t["x"] = tile["px"][0] // grid_size
        t["y"] = tile["px"][1] // grid_size
        t["t"] = tile["t"]
        level_data["tiles"].append(t)
    
    level_data["entities"] = []
    for entity in level["layerInstances"][3]["entityInstances"]:
        e = {}
        e["x"] = entity["__grid"][0]
        e["y"] = entity["__grid"][1]
        e["id"] = entity["__identifier"]
        field_instances = []
        for field in entity["fieldInstances"]:
            fi = {}
            fi["id"] = field["__identifier"]
            fi["value"] = field["__value"]
            field_instances.append(fi)        
            
        e["field_instances"] = field_instances
        level_data["entities"].append(e)
        
    json.dump(level_data, f)