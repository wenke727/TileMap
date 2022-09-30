from setuptools import setup, find_packages

# Dependencies.
with open("requirements.txt") as f:
    tests_require = f.readlines()
install_requires = [t.strip() for t in tests_require]

with open("README.md", encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="tilemap",
    version="1.1.0",
    description="Geo-tiles in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/geopandas/contextily",
    author="Wenke Huang",
    author_email="btjs727@hotmail.com",
    license="3-Clause BSD",
    packages=find_packages(),
    package_data={"": ["*.so"]},
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Framework :: Matplotlib",
    ],
    python_requires=">=3.6",
    install_requires=install_requires,
    zip_safe=False,
)