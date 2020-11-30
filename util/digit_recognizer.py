import image_process
from skimage.metrics import structural_similarity as ssim
import os
import numpy as np


class DigitRecognizer:
    def __init__(self, digit_dir: str):
        assert os.path.isdir(digit_dir), f'{digit_dir} is not a directory'
        digits = image_process.read_digit_label_dir(digit_dir)
        if len(digits) == 0:
            raise FileNotFoundError(f'No digit file was found in directory "{digit_dir}"')
        item_iter = iter(digits.items())
        first_shape = next(item_iter)[1].shape
        for _, img in item_iter:
            if img.shape != first_shape:
                raise ValueError(f'Inconsistent image shape: expected {first_shape}, but got {img.shape}')
        self.digits = digits
        self._shape = first_shape

    def recognize(self, img: np.ndarray):
        img_normalized = image_process.normalize_image(img, self._shape)
        ret_val = {k: ssim(v, img_normalized) for k, v in self.digits.items()}
        sorted_keys = sorted(ret_val, key=lambda x: ret_val[x], reverse=True)
        return sorted_keys[0]
