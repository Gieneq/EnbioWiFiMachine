from setuptools import setup, find_packages

setup(
    name="enbio_wifi_machine",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'minimalmodbus~=2.1.1',
        'pyserial~=3.5',
        'matplotlib==3.9.2',
        'pandas==2.2.3',
    ],
    entry_points={
        "console_scripts": [
            "enbio_wifi_machine=enbio_wifi_machine.cli:main",  # This creates the `modbustool` CLI command
        ]
    },
    author="Piotr Adamczyk",
    author_email="piotr.adamczyk@enbio.com",
    description="A tool to communicate and control Enbio Device via Modbus RTU.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/enbio_modbus",  # Update with your GitHub repo
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
