import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="runbook",
    version="0.1",
    description="a tool for defining repeatable processes in code",
    author="Benjamin Fagin",
    author_email="blouis@unquietcode.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/UnquietCode/runbook.py",
    packages=setuptools.find_namespace_packages(exclude=['test']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)