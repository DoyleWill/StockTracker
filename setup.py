from setuptools import setup, find_packages

setup(
    name="stocktracker",
    version="1.0.0",
    description="PiTrader - A lightweight stock tracking app",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "customtkinter",
        "finnhub-python",
        "python-dotenv",
        "Pillow",
    ],
    entry_points={
        "console_scripts": [
            "stocktracker=main:main",
        ],
    },
    python_requires=">=3.7",
)