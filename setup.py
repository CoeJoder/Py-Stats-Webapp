from setuptools import setup

setup(
    name="Ski-Stats-Webapp",
    packages=["ski_stats"],
    include_package_data=True,
    install_requires=[
        'flask',
        'pkgutil',
    ],
)
