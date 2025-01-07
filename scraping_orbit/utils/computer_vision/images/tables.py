import os
from pathlib import Path
import cv2
from img2table.document import Image as Img2TableImage
from scraping_orbit.utils import code_creation


def detect_tables(image, is_borderless=True, return_bound_boxes=False, args=None):
    """
    Detects and extracts tables from an image.

    Args:
        image (str or Path or numpy.ndarray): Path to the image file or the image as a numpy array.
        is_borderless (bool): Flag to indicate if the tables are borderless. Default is True.
        return_bound_boxes (bool): Flag to indicate if bounding boxes should be returned. Default is False.
        args (dict, optional): Additional arguments to override default parameters.

    Returns:
        list: List of cropped images of tables.
        list (optional): List of bounding box dictionaries if return_bound_boxes is True.
    """
    try:
        # Load image if path is provided
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))

        # Generate a temporary image path
        temp_img_path = f"temp_img_ocr2_{code_creation.create_random_code()}.png"
        cv2.imwrite(temp_img_path, image)

        # Override default parameters with provided arguments
        if args is not None:
            return_bound_boxes = args.get('return_bound_boxes', return_bound_boxes)
            is_borderless = args.get('is_borderless', is_borderless)

        # Instantiate the image for table extraction
        img = Img2TableImage(src=temp_img_path, detect_rotation=False)

        # Extract tables from the image
        img_tables = img.extract_tables(borderless_tables=is_borderless)
        tables_content = []
        bound_boxes = []

        for table in img_tables:
            x1, y1, x2, y2 = table.bbox.x1, table.bbox.y1, table.bbox.x2, table.bbox.y2
            cropped_image = image[y1:y2, x1:x2]

            bounding_box = {'y1': y1, 'y2': y2, 'x1': x1, 'x2': x2}
            bound_boxes.append(bounding_box)
            tables_content.append(cropped_image)

        os.remove(temp_img_path)

        if return_bound_boxes:
            return tables_content, bound_boxes
        else:
            return tables_content

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
