from setuptools import setup, find_packages

setup(
    name="yt_subs",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # aquí van tus dependencias del requirements.txt
        "requests", 
        # ...
    ],
    entry_points={
        "console_scripts": [
            "yt_subs=app.main:main"
        ]
    },
)
