import os
import pandas as pd
import tabula
from pdf2image import convert_from_path
from scraping_orbit.utils import code_creation

def pdf_to_images(pdf_path, output_path, poppler_path=None, dpi=300):
    """
    Converts each page of a PDF into an image and saves them to the specified output path.

    Args:
        pdf_path (str): Path to the input PDF file.
        output_path (str): Directory where the images will be saved.
        poppler_path (str, optional): Path to the poppler binaries. Defaults to None.
        dpi (int, optional): Resolution of the output images. Defaults to 300.

    Returns:
        list: List of paths to the saved images.
    """
    try:
        if poppler_path is not None:
            images = convert_from_path(pdf_path, poppler_path=poppler_path, dpi=dpi)
        else:
            images = convert_from_path(pdf_path, dpi=dpi)

        basecode = code_creation.create_random_code()
        images_to_return = []

        for i, image in enumerate(images):
            image_name = os.path.join(output_path, f"{basecode}_page_{i + 1}.png")
            image.save(image_name, 'PNG')
            print('Saved PDF page to image:', image_name)
            images_to_return.append(image_name)

        return images_to_return
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []

def extract_table_to_dataframe(pdf_path, pages='all'):
    """
    Extracts tables from a PDF file and returns them as DataFrames.

    Args:
        pdf_path (str): Path to the input PDF file.
        pages (str or int, optional): Pages to extract tables from. Defaults to 'all'.

    Returns:
        DataFrame or list: A single DataFrame if one table is found, otherwise a list of DataFrames.
    """
    try:
        tables = tabula.read_pdf(pdf_path, pages=pages, multiple_tables=True)
        dataframes = [pd.DataFrame(table) for table in tables]

        if len(dataframes) == 1:
            return dataframes[0]
        else:
            return dataframes
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
        return None
