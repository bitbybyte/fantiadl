import setuptools
from distutils.util import convert_path


with open("README.md", "r") as description_file:
    long_description = description_file.read()

with open("requirements.txt", "r") as requirements_file:
    requirements = requirements_file.read().split("\n")

main_ns = {}
version_path = convert_path("fantiadl/__version__.py")
with open(version_path, encoding="utf8") as version_file:
    exec(version_file.read(), main_ns)

setuptools.setup(
    name="fantiadl",
    version=main_ns["__version__"],
    description="Download posts and media from Fantia",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="bitto",
    url="https://github.com/bitbybyte/fantiadl",
    packages=["fantiadl"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: WWW/HTTP",
    ],
    license="MIT",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "fantiadl=fantiadl.fantiadl:cli"
        ]
    },
    python_requires=">=3.0",
)