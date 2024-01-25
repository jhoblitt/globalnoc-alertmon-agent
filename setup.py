from setuptools import setup

setup(
  name="globalnoc-alertmon-agent",
  version="1.0.1",
  author="GlobalNOC Systems Engineering",
  author_email="syseng@globalnoc.iu.edu",
  python_requires='>=3.8.11, <4.0.0',
  description="Facilitates the process of submitting alerts to the GlobalNOC AlertMon system.",
  url="https://github.com/GlobalNOC/globalnoc-alertmon-agent",
  license="Apache License, Version 2.0 ",
  classifiers=[
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3"
  ],
  install_requires=[
    "globalnoc_wsc==1.0.2",
    "pyyaml==6.0.1",
  ]
)
