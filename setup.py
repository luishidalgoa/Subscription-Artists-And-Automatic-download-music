from setuptools import setup, find_packages

setup(
    name="yt-subs",
    version="1.1.9",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # aquí van tus dependencias del requirements.txt
        "requests", 
        # ...
    ],
    entry_points={
        "console_scripts": [
            "yt-subs=src.main:main"
        ]
    },
)
