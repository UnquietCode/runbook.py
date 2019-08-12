import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="unquietcode-runbook",
    version="0.0",
    description="a tool for defining repeatable processes in code",
    author="Benjamin Fagin",
    author_email="blouis@unquietcode.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/UnquietCode/runbook.py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: unlicensed",
        "Operating System :: OS Independent",
    ],
)