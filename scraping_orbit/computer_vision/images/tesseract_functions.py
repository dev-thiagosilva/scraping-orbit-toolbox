import math
import traceback
from typing import Union, Tuple, Dict, Any

import cv2
import numpy as np
import pytesseract
from deskew import determine_skew


def check_confidence_tesseract(image_to_analyse: np.ndarray, tesseract_options: Dict[str, Any] = None) -> float:
    """
    Check the OCR confidence level using Tesseract.

    Args:
        image_to_analyse (np.ndarray): The image to be analyzed.
        tesseract_options (dict, optional): Tesseract configuration options.

    Returns:
        float: The average confidence score.
    """
    if tesseract_options is None:
        tesseract_options = {
            'tesseract_lang': 'por',
            'tesseract_config': "--oem 3 --psm 6",
            'use_ai_enhancement': False,
            'ai_model_short': 'gpt-3.5-turbo',
            'ai_model_large': 'gpt-3.5-turbo-16k',
            'ai_temperature': 0.5
        }

    average_confidence = 70

    try:
        data = pytesseract.image_to_data(
            image_to_analyse,
            lang=tesseract_options['tesseract_lang'],
            config=tesseract_options['tesseract_config'],
            output_type=pytesseract.Output.DICT
        )

        confidence_values = [int(data['conf'][i]) for i in range(len(data['text'])) if int(data['conf'][i]) >= 10]
        average_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else average_confidence
    except Exception as e:
        print(f"Error in check_confidence_tesseract: {e}")

    return average_confidence


def improve_image_orientation(original_image: np.ndarray, tesseract_options: Dict[str, Any] = None,
                              return_confidence_category: bool = True) -> Union[np.ndarray, Tuple[np.ndarray, str]]:
    """
    Improve the orientation of an image based on OCR confidence.

    Args:
        original_image (np.ndarray): The original image to be processed.
        tesseract_options (dict, optional): Tesseract configuration options.
        return_confidence_category (bool): Flag to return confidence category. Default is True.

    Returns:
        np.ndarray: The improved image.
        Tuple[np.ndarray, str]: The improved image and confidence category if return_confidence_category is True.
    """
    def rotate(image: np.ndarray, angle: float, background: Union[int, Tuple[int, int, int]]) -> np.ndarray:
        """
        Rotate the image by a given angle with a specified background.

        Args:
            image (np.ndarray): The image to rotate.
            angle (float): The angle by which to rotate the image.
            background (Union[int, Tuple[int, int, int]]): The background color.

        Returns:
            np.ndarray: The rotated image.
        """
        old_height, old_width = image.shape[:2]
        angle_radian = math.radians(angle)
        new_width = abs(np.sin(angle_radian) * old_height) + abs(np.cos(angle_radian) * old_width)
        new_height = abs(np.sin(angle_radian) * old_width) + abs(np.cos(angle_radian) * old_height)

        image_center = tuple(np.array(image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        rot_mat[1, 2] += (new_width - old_width) / 2
        rot_mat[0, 2] += (new_height - old_height) / 2

        return cv2.warpAffine(image, rot_mat, (int(round(new_width)), int(round(new_height))),
                              borderValue=background)

    if tesseract_options is None:
        tesseract_options = {
            'tesseract_lang': 'por',
            'tesseract_config': "--oem 3 --psm 6",
            'use_ai_enhancement': False,
            'ai_model_short': 'gpt-3.5-turbo',
            'ai_model_large': 'gpt-3.5-turbo-16k',
            'ai_temperature': 0.5
        }

    better_image = original_image
    confidence_category = 'AVERAGE'

    try:
        gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        blurred_image = cv2.GaussianBlur(gray_image, (7, 7), 0)
        thresholded_image = cv2.adaptiveThreshold(blurred_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 10)
        inverted_image = cv2.bitwise_not(thresholded_image)

        angles_and_confidences = []

        for rotation in [0, 90, 180, 270]:
            rotated_image = cv2.rotate(inverted_image, rotation)
            skew_angle = determine_skew(rotated_image)
            deskewed_image = rotate(rotated_image, skew_angle, (0, 0, 0))
            confidence = check_confidence_tesseract(deskewed_image, tesseract_options)
            rotated_original = cv2.rotate(original_image, rotation)
            angles_and_confidences.append((confidence, rotated_original))

        best_confidence, best_image = max(angles_and_confidences, key=lambda item: item[0])
        better_image = best_image

        if best_confidence <= 40:
            confidence_category = 'BAD'
        elif 41 <= best_confidence <= 70:
            confidence_category = 'AVERAGE'
        elif 71 <= best_confidence <= 100:
            confidence_category = 'GOOD'

    except Exception as e:
        print(f"Error in improve_image_orientation: {e}")
        print(traceback.format_exc())

    return (better_image, confidence_category) if return_confidence_category else better_image


def visualize_image(image: np.ndarray, window_size: Tuple[int, int] = (800, 950)) -> None:
    """
    Display an image using OpenCV.

    Args:
        image (np.ndarray): The image to display.
        window_size (tuple): The size of the display window. Default is (800, 950).
    """
    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('image', window_size)
    cv2.imshow('image', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
