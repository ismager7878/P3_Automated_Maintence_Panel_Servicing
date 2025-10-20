import yaml
import spatialmath as spm
import numpy as np

def quaternion2axis_angle(e1, e2, e3, e4):
    q = spm.UnitQuaternion([e4, e1, e2, e3])
    R = q.R

    np.set_printoptions(precision=4, suppress=True)  # Set print options for better readability

    r_mat = spm.SO3(R)

    return r_mat

Rmat = quaternion2axis_angle(0.064071, 0.091158, 0.15344, 0.98186)

print(f"rotation matrix:")
print(Rmat)

# Åbn og læs YAML-filen
def yaml_files(R_matrix):
    R_mat = R_matrix.R
    
    datasetPose = [
        {
            "id": 1,
            "rotation": [
                [1, 2, 3],
                [4, 5, 6],
                [7, 8, 9]
            ],
            "translation": [
                [9, 8, 7]
            ]
        }
    ]

    quaternionData = [
        {
            "id": 1,
            "rotation": R_mat.tolist()
        }
    ]
    return quaternionData

data = yaml_files(Rmat)

path = "/home/petur/Documents/Github/P3_Automated_Maintence_Panel_Servicing/src/amps-python/amps-python/data/calibration-data/camera_calibration.yaml"

# Skriv YAML-filen
with open(path, "w") as file:
    yaml.dump(data, file)

# Læs YAML-filen igen
with open(path, "r") as file:
    loaded_data = yaml.safe_load(file)

# Print indholdet som et Python dictionary
print(loaded_data)

