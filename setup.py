from pathlib import Path
import setuptools

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setuptools.setup(
    name="scraping-orbit",
    version="0.0.1",
    author="Thiago Silva",
    author_email="",
    description="Tools for web-scraping and automation projects.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thiagosilva977/scraping-orbit-toolbox",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[],
    python_requires=">=3.10",
    install_requires=[
        "streamlit>=0.63",
    ],
)
