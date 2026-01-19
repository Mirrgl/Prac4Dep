from setuptools import setup, find_packages

setup(
    name="siem-web",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "python-dotenv>=1.0.0",
        "jinja2>=3.1.0",
        "python-multipart>=0.0.6",
    ],
)
