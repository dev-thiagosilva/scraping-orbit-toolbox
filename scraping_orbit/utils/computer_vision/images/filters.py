import math
import os
from pathlib import Path
from typing import Union, Tuple, Dict, Any

import cv2
import numpy as np
from deskew import determine_skew

# Define global paths
global_assets_path = Path(__file__).resolve().parent.parent.parent / 'assets'
upscaling_model_path = str(global_assets_path / 'ESPCN_x2.pb')


def upscale_image(image: np.ndarray,
                  upscale_model_file: str = upscaling_model_path,
                  model_name: str = "espcn",
                  scale: int = 2,
                  interpolation: int = cv2.INTER_CUBIC) -> np.ndarray:
    """
    Upscales an image using a specified super-resolution model.
    """
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(upscale_model_file)
    sr.setModel(model_name, scale)
    result = sr.upsample(image)
    upscaled_image = cv2.resize(result, dsize=None, fx=scale, fy=scale, interpolation=interpolation)
    return upscaled_image


def reduce_noise(image: np.ndarray) -> np.ndarray:
    """
    Applies noise reduction to the image.
    """
    return cv2.fastNlMeansDenoising(image)


def adjust_contrast_brightness(image: np.ndarray, alpha: float = 1.0, beta: int = 0) -> np.ndarray:
    """
    Adjusts the contrast and brightness of the image.
    """
    return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)


def equalize_histogram(image: np.ndarray) -> np.ndarray:
    """
    Applies histogram equalization to the image.
    """
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.equalizeHist(gray_image)


def apply_gaussian_blur(image: np.ndarray, kernel_size: Tuple[int, int] = (5, 5)) -> np.ndarray:
    """
    Applies Gaussian blur to the image.
    """
    return cv2.GaussianBlur(image, kernel_size, 0)


def detect_edges_canny(image: np.ndarray, threshold1: int = 100, threshold2: int = 200) -> np.ndarray:
    """
    Detects edges in the image using the Canny edge detection algorithm.
    """
    return cv2.Canny(image, threshold1, threshold2)


def correct_perspective(image: np.ndarray, src_points: np.ndarray, dst_points: np.ndarray) -> np.ndarray:
    """
    Applies perspective correction to the image.
    """
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    return cv2.warpPerspective(image, matrix, (image.shape[1], image.shape[0]))


def sharpen_image(image: np.ndarray) -> np.ndarray:
    """
    Sharpens the image using a predefined kernel.
    """
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    return cv2.filter2D(image, -1, kernel)


def convert_to_gray(image: np.ndarray) -> np.ndarray:
    """
    Converts the image to grayscale.
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def apply_threshold(image: np.ndarray, max_value: int = 255, adaptive_method: int = cv2.ADAPTIVE_THRESH_MEAN_C,
                    threshold_type: int = cv2.THRESH_BINARY, block_size: int = 31, c: int = 10) -> np.ndarray:
    """
    Applies adaptive thresholding to the image.
    """
    return cv2.adaptiveThreshold(image, max_value, adaptive_method, threshold_type, block_size, c)


def invert_colors(image: np.ndarray) -> np.ndarray:
    """
    Inverts the colors of the image.
    """
    return cv2.bitwise_not(image)


def remove_table_lines(image: np.ndarray, options: Dict[str, int] = None) -> np.ndarray:
    """
    Removes table lines from the image.
    """
    if options is None:
        options = {'manual_table_dilate_iterations': 10, 'manual_table_erode_iterations': 10}

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresholded_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                              cv2.THRESH_BINARY, 31, 10)
    inverted_image = cv2.bitwise_not(thresholded_image)

    hor_kernel = np.array([[1, 1, 1, 1, 1, 1]])
    ver_kernel = np.array([[1], [1], [1], [1], [1], [1], [1]])

    vertical_lines = cv2.erode(inverted_image, hor_kernel, iterations=options['manual_table_erode_iterations'])
    vertical_lines = cv2.dilate(vertical_lines, hor_kernel, iterations=options['manual_table_dilate_iterations'])

    horizontal_lines = cv2.erode(inverted_image, ver_kernel, iterations=options['manual_table_erode_iterations'])
    horizontal_lines = cv2.dilate(horizontal_lines, ver_kernel, iterations=options['manual_table_dilate_iterations'])

    combined_lines = cv2.add(vertical_lines, horizontal_lines)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    dilated_lines = cv2.dilate(combined_lines, kernel, iterations=5)

    lines_removed = cv2.subtract(inverted_image, dilated_lines)

    lines_removed = cv2.erode(lines_removed, kernel, iterations=1)
    lines_removed = cv2.dilate(lines_removed, kernel, iterations=1)

    return lines_removed


def select_bounding_boxes(image: np.ndarray, target_name: str = '') -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Manually selects bounding boxes from the image.
    """
    zoom_out_factor = 4
    resized_image = cv2.resize(image, (image.shape[1] // zoom_out_factor, image.shape[0] // zoom_out_factor))

    window_name = f"TARGET> {target_name}"
    roi = cv2.selectROI(window_name, resized_image)

    x1, y1, w, h = roi
    x2, y2 = x1 + w, y1 + h

    cropped_resized = resized_image[y1:y2, x1:x2]
    cropped_original = image[y1 * zoom_out_factor:y2 * zoom_out_factor, x1 * zoom_out_factor:x2 * zoom_out_factor]

    cv2.imshow("Cropped", cropped_resized)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    cv2.imshow("Cropped Original", cropped_original)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return cropped_original, {'x1': x1 * zoom_out_factor, 'y1': y1 * zoom_out_factor,
                              'x2': x2 * zoom_out_factor, 'y2': y2 * zoom_out_factor}


def correct_skew(image: np.ndarray) -> np.ndarray:
    """
    Corrects the skew of the image.
    """

    def rotate(image: np.ndarray, angle: float, background: Union[int, Tuple[int, int, int]] = (0, 0, 0)) -> np.ndarray:
        old_height, old_width = image.shape[:2]
        angle_radian = math.radians(angle)
        new_width = int(abs(math.sin(angle_radian) * old_height) + abs(math.cos(angle_radian) * old_width))
        new_height = int(abs(math.sin(angle_radian) * old_width) + abs(math.cos(angle_radian) * old_height))

        image_center = (old_width / 2, old_height / 2)
        rotation_matrix = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        rotation_matrix[1, 2] += (new_height - old_height) / 2
        rotation_matrix[0, 2] += (new_width - old_width) / 2

        return cv2.warpAffine(image, rotation_matrix, (new_width, new_height), borderValue=background)

    skew_angle = determine_skew(image)
    return rotate(image, skew_angle)


if __name__ == '__main__':
    img_test_path = global_assets_path / 'img_test.jpg'
    image = cv2.imread(str(img_test_path))

    if image is not None:
        upscaled_image = upscale_image(image)
        cv2.imshow("Upscaled Image", upscaled_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print(f"Image at {img_test_path} could not be loaded.")
