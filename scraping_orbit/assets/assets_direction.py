import os

current_dir = os.path.dirname(os.path.abspath(__file__))
roaming_appdata_path = str(os.getenv('APPDATA')).replace('Roaming', 'Local')
poppler_path = f"{roaming_appdata_path}\\scraping_orbit_extras\\poppler-24.07.0\\Library\\bin"
upscaler_file = f"{current_dir}\\ESPCN_x2.pb"
tesseract_installed = f"{roaming_appdata_path}\\scraping_orbit_extras\\Tesseract-OCR\\tesseract.exe"
wkhtmltopdf = f"{roaming_appdata_path}\\scraping_orbit_extras\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
