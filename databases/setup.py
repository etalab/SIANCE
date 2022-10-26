from setuptools import setup, find_packages

setup(
    name="Siance Database",
    version="0.1.0",
    packages=find_packages(),
    scripts=["bin/siance-db"],
    # url="http://pypi.python.org/pypi/PackageName/",
    url="http://siance.asn.i2",
    license="LICENSE.txt",
    description="Database management tool for the SIANCE project",
    long_description=open("README.txt").read(),
    install_requires=[
        "altair",
        "xlsxwriter",
        "click",
        "pydantic",
        "sqlalchemy",
        "psycopg2-binary",
        "elasticsearch",
        "pytest",
    ],
)
