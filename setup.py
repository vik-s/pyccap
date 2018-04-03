from setuptools import setup
setup(
    name="pyccap",
    version="0.1",

    # metadata for upload to PyPI
    author="Vikram Sekar",
    author_email="vikram.mail@gmail.com",
    description="Open source project to emulate the functionality of Keysight's ICCAP device modeling software.",
    license="MIT",
    keywords="electronics instrument gpib semiconductor device",
    url="http://github.com/vik-s/pyccap",   # project home page, if any
    install_requires=['numpy','matplotlib','pyvisa','scikit-rf'],
)
