from attacher import MumuScreenCapturer
import matplotlib.pyplot as plt
import image_process
import resolution_adapter
from basic_class import Resolution


if __name__ == '__main__':
    img = MumuScreenCapturer().get_screenshot()
    detection_defs = resolution_adapter.DetectionDefFactory.get_detection_def(Resolution(img.shape[0], img.shape[1]))
    target_resolution = detection_defs.get_target_resolution()
    if target_resolution is not None:
        img = image_process.resize(img, target_resolution.width, target_resolution.height)
    img = resolution_adapter.plot_detection_rects_and_click_points(img)
    img = img.copy()

    # for i in range(0, img.shape[0], 10):
    #     img[i, :, 0] = 255
    # for i in range(0, img.shape[1], 10):
    #     img[:, i, 1] = 255

    dpi = plt.rcParams['figure.dpi']
    fig = plt.figure(figsize=(img.shape[1] / dpi * 1.1, img.shape[0] / dpi * 1.1))
    plt.imshow(img)
    plt.show()
