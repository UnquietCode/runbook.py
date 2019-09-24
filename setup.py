import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="runbook",
    version="0.1",
    description="a tool for defining repeatable processes in code",
    author="Benjamin Fagin",
    author_email="blouis@unquietcode.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/UnquietCode/runbook.py",
    keywords="runbook playbook process",
    packages=setuptools.find_namespace_packages(exclude=['test']),
    install_requires=requirements,
    license='OSI Approved :: Apache Software License'
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)