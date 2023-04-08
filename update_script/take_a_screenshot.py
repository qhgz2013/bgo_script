from attacher import ADBScreenCapturer, MumuScreenCapturer
import matplotlib.pyplot as plt
import image_process
import resolution_adapter
from basic_class import Resolution
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--grid', action='store_true', help='Show grid')
    parser.add_argument('--capturer', choices=['adb_native', 'mumu'], default='mumu', type=str)
    args, _ = parser.parse_known_args()
    cap_dict = {'adb_native': ADBScreenCapturer, 'mumu': MumuScreenCapturer}
    cap = cap_dict[args.capturer]()
    img = cap.get_screenshot()
    detection_defs = resolution_adapter.DetectionDefFactory.get_detection_def(Resolution(img.shape[0], img.shape[1]))
    target_resolution = detection_defs.get_target_resolution()
    if target_resolution is not None:
        img = image_process.resize(img, target_resolution.width, target_resolution.height)
    if args.grid:
        img = img.copy()
        for i in range(0, img.shape[0], 10):
            img[i, :, 0] = 255
        for i in range(0, img.shape[1], 10):
            img[:, i, 1] = 255
    else:
        img = resolution_adapter.plot_detection_rects_and_click_points(img)

    dpi = plt.rcParams['figure.dpi']
    fig = plt.figure(figsize=(img.shape[1] / dpi * 1.1, img.shape[0] / dpi * 1.1))
    plt.imshow(img)
    plt.show()
