import yaml
import spatialmath as spm
import numpy as np

def quaternion2axis_angle(e1, e2, e3, e4):
    q = spm.UnitQuaternion([e4, e1, e2, e3])
    R = q.R

    np.set_printoptions(precision=4, suppress=True)  # Set print options for better readability

    r_mat = spm.SO3(R)
    theta, Kt = r_mat.angvec()

    return Kt, theta

Kt, theta = quaternion2axis_angle(0.064071, 0.091158, 0.15344, 0.98186)

print("Axis angle from quaternion:")
print(f"theta: {theta}")
print(f"Kt: {Kt}")

def yaml_files():

    # Åbn og læs YAML-filen
    with open("/home/petur/Documents/Github/P3_Automated_Maintence_Panel_Servicing/src/amps-python/amps-python/data/calibration-data/camera_calibration.yaml", "r") as file:
        data = yaml.safe_load(file)

    # Print indholdet som et Python dictionary
    print(data)

