from basic_class import Resolution
from .base import ScreenCapturer
import numpy as np

__all__ = ['MockCapturer']


class MockCapturer(ScreenCapturer):

    def __init__(self, img: np.ndarray):
        assert len(img.shape) == 3, 'Image should be in (h, w, c) shape'
        self._img = img

    @property
    def img(self) -> np.ndarray:
        return self._img

    @img.setter
    def img(self, new_img: np.ndarray):
        assert len(new_img) == 3, 'Image should be in (h, w, c) shape'
        self._img = new_img

    def get_resolution(self) -> Resolution:
        return Resolution(self._img.shape[0], self._img.shape[1])

    def get_screenshot(self) -> np.ndarray:
        return self._img.copy()
