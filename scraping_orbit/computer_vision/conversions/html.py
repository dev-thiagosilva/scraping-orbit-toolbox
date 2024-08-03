import base64
import os
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import pdfkit

from scraping_orbit.computer_vision.conversions.pdf import pdf_to_images
from scraping_orbit.utils import code_creation

# Global paths
GLOBAL_ASSETS_PATH = Path(os.path.abspath(__file__)).parent.parent.parent.joinpath('assets')
GLOBAL_POPPLER_PATH = str(GLOBAL_ASSETS_PATH.joinpath('poppler-23.08.0', 'Library', 'bin'))


def extract_text_from_pdf(pdf_file):
    """
    Extracts text from a PDF file.

    Args:
        pdf_file (str): Path to the PDF file.

    Returns:
        list: A list containing text from each page of the PDF.
    """
    pdf_text = []
    with open(pdf_file, 'rb') as pdf:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            pdf_text.append(page.extract_text())
    return pdf_text


def format_html_elements_to_pattern(html_content, pattern_number=0):
    """
    Formats HTML content according to a specified pattern.

    Args:
        html_content (str or BeautifulSoup): The HTML content to format.
        pattern_number (int): The pattern number to apply.

    Returns:
        BeautifulSoup: The formatted HTML content.
    """
    if isinstance(html_content, str):
        html_content = BeautifulSoup(html_content, 'html.parser')

    if pattern_number == 0:
        tags_to_remove = ['link', 'button', 'noscript', 'script']
        for tag in tags_to_remove:
            for element in html_content.find_all(tag):
                element.extract()

        for element in html_content.find_all('a'):
            element.attrs.pop('href', None)

        for element in html_content.find_all('img'):
            if element.get('src', '').startswith('/'):
                element.attrs.pop('src', None)

        for table in html_content.find_all('table'):
            attrs_to_remove = ['width', 'height', 'cellspacing', 'cellpadding', 'border', 'style']
            for attr in attrs_to_remove:
                table.attrs.pop(attr, None)
            table.attrs.update({
                'cellspacing': '2',
                'cellpadding': '8',
                'border': '0',
                'style': 'font-family: Arial; page-break-inside: avoid;'
            })

            if table.find('thead') is None and (first_row := table.find('tr')) is not None:
                thead = BeautifulSoup('<thead></thead>', 'html.parser')
                thead.append(first_row.extract())
                table.insert(0, thead)
            if thead := table.find('thead'):
                thead.attrs['style'] = 'display: table-header-group;'

        for element in html_content.find_all('p'):
            element.attrs.pop('style', None)
            text_content = element.get_text(strip=True)
            if text_content in ["", " ", "\n", " "]:
                text_content = "None"
            element.string = text_content
            element.attrs.update({
                'style': 'font-family: Arial; font-size: 12px;' if text_content == "None" else 'font-family: Arial; font-size: 14px;',
                'text-align': 'center',
                'vertical-align': 'center'
            })

        for element in html_content.find_all(['td', 'th']):
            attrs_to_remove = ['width', 'valign', 'style', 'border-collapse']
            for attr in attrs_to_remove:
                element.attrs.pop(attr, None)
            element.attrs.update({
                'valign': 'bottom' if element.name == 'td' else 'center',
                'border-collapse': 'collapse',
                'style': 'font-family: Arial;'
            })

        for table in html_content.find_all('table'):
            preceding_text = []
            for sibling in table.find_all_previous():
                if sibling.name in ['table', 'tbody', 'tr', 'td', 'body', 'head', 'label']:
                    break
                preceding_text.append(sibling.get_text(strip=True))
            preceding_text.reverse()
            full_text = "\n".join(preceding_text[1:])
            if full_text:
                p_tag = html_content.new_tag('p')
                p_tag.string = f'Informação anterior associada a tabela abaixo: {full_text}'
                p_tag.attrs.update({'style': 'font-family: Arial; font-size: 10px;'})
                table.find('tbody').insert(0, p_tag)

    return html_content


def html_to_images(html, pattern_number=0, poppler_path=None, wkhtml_exe=None):
    """
    Converts HTML content to images.

    Args:
        html (str): HTML content to convert.
        pattern_number (int): Pattern number for formatting the HTML.
        poppler_path (str, optional): Path to the poppler binaries.
        wkhtml_exe (str, optional): Path to the wkhtmltopdf executable.

    Returns:
        list: List of paths to the created images.
    """
    output_image_dir = Path(__file__).resolve().parent.parent.joinpath('temp_images_pdf')
    output_image_dir.mkdir(parents=True, exist_ok=True)
    output_image_dir = str(output_image_dir)

    html = format_html_elements_to_pattern(html_content=html, pattern_number=pattern_number)
    temp_pdf_path = f'{output_image_dir}/tempdf_{code_creation.create_random_code()}.pdf'

    if wkhtml_exe is not None:
        config = pdfkit.configuration(wkhtmltopdf=wkhtml_exe)
    else:
        config = pdfkit.configuration()

    options = {
        'page-size': 'A4',
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'encoding': 'UTF-8'
    }

    try:
        pdfkit.from_string(str(html), temp_pdf_path, options=options, configuration=config)
    except:
        options['enable-local-file-access'] = ""
        temp_html_path = f'{output_image_dir}/tempdf_{code_creation.create_random_code()}.html'
        with open(temp_html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(BeautifulSoup(str(html), 'html.parser').prettify())
        pdfkit.from_file(temp_html_path, temp_pdf_path, options=options, configuration=config)

    if poppler_path is not None:
        images_created = pdf_to_images(pdf_path=temp_pdf_path, output_path=output_image_dir, poppler_path=poppler_path)
    else:
        images_created = pdf_to_images(pdf_path=temp_pdf_path, output_path=output_image_dir)

    return images_created


def save_soup_to_html(path_to_save, soup_content, encoding_type='utf-8'):
    """
    Saves BeautifulSoup content to an HTML file.

    Args:
        path_to_save (str): Path to save the HTML file.
        soup_content (BeautifulSoup): The BeautifulSoup content to save.
        encoding_type (str): The encoding type for the file.

    Returns:
        str: Path to the saved HTML file.
    """
    try:
        with open(path_to_save, 'w', encoding=encoding_type) as file:
            file.write(str(soup_content))
        return path_to_save
    except Exception as e:
        print(f"Error saving HTML file: {e}")
        return None


def save_images_from_soup(soup, source_name_selected='Default'):
    """
    Extracts and saves images from BeautifulSoup content.

    Args:
        soup (BeautifulSoup): The BeautifulSoup content to extract images from.
        source_name_selected (str): The folder name to save the images in.

    Returns:
        list: List of dictionaries containing paths to saved images and metadata.
    """
    output_folder = Path(__file__).resolve().parent.parent.joinpath('temp_images_found', source_name_selected)
    output_folder.mkdir(parents=True, exist_ok=True)
    temporary_ocr_path = output_folder.joinpath('ocr_temp_folder')
    temporary_ocr_path.mkdir(parents=True, exist_ok=True)
    output_folder = str(output_folder)
    images_found = []

    img_tags = soup.find_all('img')

    for idx, img_tag in enumerate(img_tags):
        img_data = img_tag.get('src')
        if img_data and '.gif' not in img_data:
            try:
                img_format, img_data = img_data.split(';base64,')
                img_extension = img_format.split('/')[-1]
            except ValueError:
                try:
                    response = requests.get(img_data, timeout=8)
                    response.raise_for_status()
                    img_extension = img_data.split('.')[-1]
                    img_data = base64.b64encode(response.content).decode('utf-8')
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching the image: {e}")
                    continue

            img_filename = f'{code_creation.create_custom_hashid(string_hashcode=img_data)}.{img_extension}'
            img_path = os.path.join(output_folder, img_filename)
            img_filename_processed = f'{code_creation.create_custom_hashid(string_hashcode=img_data)}_processed.{img_extension}'
            img_filename_txt = f'{code_creation.create_custom_hashid(string_hashcode=img_data)}_textprocessed.txt'

            with open(img_path, 'wb') as img_file:
                img_file.write(base64.b64decode(img_data))

            images_found.append({
                'original_image': img_path,
                'processed_image': os.path.join(output_folder, img_filename_processed),
                'processed_image_exist': os.path.exists(os.path.join(output_folder, img_filename_processed)),
                'text_image': os.path.join(output_folder, img_filename_txt),
                'text_image_exist': os.path.exists(os.path.join(output_folder, img_filename_txt))
            })
        else:
            print("Image tag has no base64 data or is a GIF")

    continuation_list = [
        images_found[i]['soup'].find_next() == images_found[i + 1]['soup']
        if i + 1 < len(images_found) else False
        for i in range(len(images_found))
    ]

    for i, img in enumerate(images_found):
        img.pop('soup', None)
        img['next_image_is_continuation'] = continuation_list[i]

    return images_found
