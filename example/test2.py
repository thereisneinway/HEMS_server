import json

with open('energy_comparison_model.txt', 'w') as energy_file:
    energy_file.write(json.dumps({"Model 1": 220,"Model 2": 230,"Model 3": 240,"Real": 300}))


print(json.load(open("energy_comparison_model.txt")))