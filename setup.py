from setuptools import setup, find_packages


def read_version():
    """Read the version listed in the __init__.py file of the package."""
    init_file = open('correlogram_tools/__init__.py')
    init_lines = init_file.readlines()
    init_file.close()
    for line in init_lines:
        if 'version' in line:
            version = line.split("=")[-1].strip()[1:-1]
            break
    return str(version)

setup(
    name='correlogram_tools',
    version=read_version(),
    description='Generate correlograms and simulated raw and reconstructed images for dark field interferometry.',
    url='https://github.com/usnistgov/correlogram_tools',
    author='Caitlyn Wolf',
    author_email='caitlyn.wolf@nist.gov',
    packages=find_packages(include=["correlogram_tools", "correlogram_tools.*"]),
    #packages=find_packages(where="correlogram_tools"),
    package_data={"": ["component_library/*.json", "sasmodels_defaults/*.json"]},
    entry_points={
        'console_scripts': [
            'correlogram_sim = correlogram_tools.simulation:main',
        ],
    },
    install_requires=[
        "h5py",# == 3.4.0",
        "ipywidgets",
        "matplotlib",
        "numpy",
        "scipy", # scipy.special.j0
        "pillow",
        "plotly == 5.15.0",
        "pyopencl",
        "opencv-python",
        "bumps == 0.8.0",
        "periodictable == 1.6.0",
        "sasmodels == 1.0.5",
        # "ipykernel == 6.4.1",
        # "jupyter == 1.0.0",
        # "sphinx",
    ],
    python_requires='>= 3.10',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.8',
    ],
)
