from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'amps_python'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # install any python launch files so `ros2 launch <pkg> <file>` can find them
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'data', 'calibration-data'),
            glob('amps_python/data/calibration-data/*.xml')),
        (os.path.join('share', package_name, 'launch'),
            glob('amps_python/launch/*.launch.py')),
        ('share/amps_python/npy_files', [
        'amps_python/position/npy_files/scaler_mean.npy',
        'amps_python/position/npy_files/scaler_scale.npy',
        'amps_python/position/npy_files/features.npy',
        'amps_python/position/npy_files/labels.npy',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='lukas',
    maintainer_email='lukas@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'realsense_node = amps_python.realsense_node:main',
            'gripper_node = amps_python.gripper_node.gripper_node:main',
            'gripper_test_client = amps_python.gripper_node.gripper_test_client:main',
            'Handeye = amps_python.position.Handeye:main',
            "GUI = amps_python.GUI.GUI:main",
            'preprocessing_node = amps_python.preprocessing_node.preprocessing_node:main',
            'classified_image = amps_python.position.object_classification:main',
            "classi_test = amps_python.test.classification_test:main"
        ],
    },
)


#launch_files