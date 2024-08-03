import os
import random
import time
from pathlib import Path

import mammoth
import requests
from pdf2docx import Converter
from pyhtml2pdf import converter

def download_and_convert_document(url: str, save_dir: str, filename: str, doc_type: str,
                                  pdf_password=None, html_encoding='utf-8', request_headers=None,
                                  request_proxies=None, request_cookies=None, request_timeout=10) -> str:
    """
    Downloads a PDF or HTML file from the given URL and optionally converts between formats.

    :param url: URL to download the file from.
    :param save_dir: Directory to save the downloaded file.
    :param filename: Name of the file to save.
    :param doc_type: Document type to save as ('pdf' or 'html').
    :param pdf_password: Optional password for encrypted PDFs.
    :param html_encoding: Encoding to use for HTML files.
    :param request_headers: Optional HTTP headers for the request.
    :param request_proxies: Optional proxies for the request.
    :param request_cookies: Optional cookies for the request.
    :param request_timeout: Timeout for the request in seconds.
    :return: Path to the saved file, or None if an error occurred.
    """
    if not url or not save_dir or not filename or doc_type not in ['pdf', 'html']:
        print("Mandatory parameters are not completed or invalid document type.")
        return None

    try:
        response = requests.get(url, headers=request_headers, proxies=request_proxies,
                                cookies=request_cookies, timeout=request_timeout)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError) as error:
        print(f"An error occurred accessing the URL: {error}")
        return None

    os.makedirs(save_dir, exist_ok=True)
    save_file_path = os.path.join(save_dir, f"{filename}.{doc_type}")

    try:
        content_type = response.headers.get('content-type', '')

        if 'html' in content_type and doc_type == 'pdf':
            converter.convert(url, save_file_path)
        elif 'pdf' in content_type and doc_type == 'html':
            temp_dir = Path(save_dir).joinpath('temp_pdf_to_html')
            temp_dir.mkdir(parents=True, exist_ok=True)

            temp_pdf_file = str(temp_dir.joinpath(f"{random.randint(1, 999999)}.pdf"))
            with open(temp_pdf_file, 'wb') as f:
                f.write(response.content)
                time.sleep(0.5)

            temp_docx_file = str(temp_dir.joinpath(f"{random.randint(1, 999999)}.docx"))
            converter = Converter(temp_pdf_file, password=pdf_password)
            converter.convert(temp_docx_file, start=0, end=None)
            converter.close()

            with open(temp_docx_file, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value
                with open(save_file_path, 'w', encoding=html_encoding) as html_file:
                    html_file.write(html_content)

            os.remove(temp_docx_file)
            os.remove(temp_pdf_file)
        else:
            with open(save_file_path, 'wb') as file:
                file.write(response.content)

        print(f"Successfully downloaded: '{filename}.{doc_type}'")
        return save_file_path
    except Exception as error:
        print(f"Error saving file: {error}")
        return None
