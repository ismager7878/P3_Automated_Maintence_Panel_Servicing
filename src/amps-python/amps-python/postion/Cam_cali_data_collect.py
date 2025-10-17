import yaml

# Åbn og læs YAML-filen
with open("/home/petur/Documents/Github/P3_Automated_Maintence_Panel_Servicing/src/amps-python/amps-python/data/calibration-data/camera_calibration.yaml", "r") as file:
    data = yaml.safe_load(file)

# Print indholdet som et Python dictionary
print(data)