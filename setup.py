from pathlib import Path
from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

REQUIRED_PKGS = [
    'beautifulsoup4',
    'click',
    'lxml',
    'numpy',
    'pandas',
    'pyarrow',
    'requests',
    'streamlit>=1.37.0',
    'xlrd',
    "opencv-contrib-python==4.10.0.82",
    "opencv-python==4.10.0.82",
    "fastapi",
    "pypdl",
    'matplotlib',
    'nltk',
    'openai',
    'tiktoken',
    'scikit-learn',
    'plotly',
    'spacy',
    'pyjwt',
    'httpx',
    'openpyxl',
    'Unidecode',
    "python-dateutil",
    'streamlit-audiorec',
    'faster-whisper',
    'pydub',
    'numba',
    'accelerate',
    "pdfplumber"

]
EXTRAS_REQUIRE = {
    "full": [
        "torchvision",
        'langchain'
        , "awswrangler"
        , "beautifulsoup4"
        , "boto3"
        , "botocore"
        , "pymongo"
        , "Brotli"
        , "bs4"
        , "certifi"
        , "charset-normalizer"
        , "click"
        , "cobble"
        , "colorama"
        , "deskew"
        , "distro"
        , "dm-tree"
        , "dnspython"
        , "emoji"
        , "et-xmlfile"
        , "fastparquet"
        , "html2image"
        , "huggingface-hub"
        , "hyperframe"
        , "imageio"
        , "img2table"
        , "JPype1"
        , "lxml"
        , "matplotlib"
        , "nltk"
        , "numpy"
        , "openai"
        , "opencv-contrib-python==4.10.0.82"
        , "opencv-python==4.10.0.82"
        , "openpyxl"
        , "pandas"
        , "pdf2docx"
        , "pdf2image"
        , "pdfkit"
        , "pdfminer.six"
        , "Pillow"
        , "plotly"
        , "pyarrow"
        , "pyhtml2pdf"
        , "PyMuPDF"
        , "PyPDF2"
        , "PySocks"
        , "pytesseract"
        , "python-docx"
        , "python-dotenv"
        , "pytz"
        , "pyxlsb"
        , "PyYAML"
        , "regex"
        , "reportlab"
        , "requests"
        , "requests-oauthlib"
        , "safetensors"
        , "scikit-image"
        , "scikit-learn"
        , "shapely"
        , "six"
        , "streamlit>=1.37.0"
        , "tabula-py"
        , "tensorboard"
        , "tensorboard-data-server"
        , "tensorflow"
        , "tiktoken"
        , "tokenizers"
        , "toml"
        , "tornado"
        , "transformers"
        , "unicode"
        , "Unidecode"
        , "watchdog"
        , "xlrd"
        , "xlsx2html"
        , "XlsxWriter"
        , "zipp"
        , "zstandard"
          "spacy",
        "einops",
        "sentencepiece",
        "accelerate",
        "GPUtil",
        "streamlit-authenticator",
        "streamlit-card",
        "streamlit-feedback",
        "numpy",
        "mammoth",
        "streamlit-agraph",
        "streamlit-feedback",
        "undetected-chromedriver",
        "playwright",
        "pdfplumber",
    ]}

setup(
    name="scraping-orbit",
    version="0.0.3",
    author="Thiago Silva",
    author_email="",
    description="Tools for web-scraping and automation projects.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thiagosilva977/scraping-orbit-toolbox",
    packages=find_packages(),
    classifiers=[],
    python_requires=">=3.11",
    install_requires=REQUIRED_PKGS,
    extras_require=EXTRAS_REQUIRE,
    include_package_data=True,
    zip_safe=False,
    package_data={'my_package': ['scraping_orbit/assets/ESPCN_x2.pb',
                                 'scraping_orbit/assets/img_test.jpg'
                                 ]
                  },
)
