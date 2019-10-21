import cv2
import skimage.io
import numpy as np
from cv_positioning import *
import matplotlib.pyplot as plt
import sqlite3
from io import BytesIO
from PIL import Image
import pickle


def sample():
    img = skimage.io.imread(r'C:\Users\qhgz2\Documents\MuMu共享文件夹\MuMu20191021151504.png')[..., :3]
    img = cv2.resize(img, (1280, 720))
    img2 = skimage.io.imread(r'Z:\craft_essence\礼装261.jpg')
    x1 = int(CV_SCREENSHOT_RESOLUTION_X * CV_SUPPORT_SERVANT_X1)
    x2 = int(CV_SCREENSHOT_RESOLUTION_X * CV_SUPPORT_SERVANT_X2)
    support = img[198:375, x1:x2, :]
    support = cv2.resize(support, (132, 144), interpolation=cv2.INTER_CUBIC)
    craft_essence = support[105:-3, ...]
    detector = cv2.xfeatures2d_SIFT.create()
    kp1, d1 = detector.detectAndCompute(craft_essence, None)
    kp2, d2 = detector.detectAndCompute(img2, None)

    matcher = cv2.DescriptorMatcher_create(cv2.DescriptorMatcher_FLANNBASED)
    knn_matches = matcher.knnMatch(d1, d2, 2)
    ratio_thresh = 0.7
    good_matches = []
    for m, n in knn_matches:
        if m.distance < ratio_thresh * n.distance:
            good_matches.append(m)
    img_matches = np.empty((max(craft_essence.shape[0], img2.shape[0]), craft_essence.shape[1] + img2.shape[1], 3),
                           dtype=np.uint8)
    cv2.drawMatches(craft_essence, kp1, img2, kp2, good_matches, img_matches,
                    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    plt.figure()
    plt.imshow(img_matches)
    plt.show()


def serialize_cv2_keypoint(point):
    return point.pt, point.size, point.angle, point.response, point.octave, point.class_id


def deserialize_cv2_keypoint(serialized_tuple):
    return cv2.KeyPoint(x=serialized_tuple[0][0], y=serialized_tuple[0][1], _size=serialized_tuple[1],
                        _angle=serialized_tuple[2], _response=serialized_tuple[3], _octave=serialized_tuple[4],
                        _class_id=serialized_tuple[5])


def main():
    conn = sqlite3.connect('cv_data/fgo.db')
    csr = conn.cursor()
    csr.execute("select image_key from craft_essence_icon")
    keys = [x[0] for x in csr.fetchall()]
    detector = cv2.xfeatures2d_SIFT.create()
    for key in keys:
        csr.execute("select image_data from image where image_key = ?", (key,))
        blob_data = csr.fetchone()[0]
        img = np.asarray(Image.open(BytesIO(blob_data)))
        key_points, descriptor = detector.detectAndCompute(img, None)
        key_point_blob = pickle.dumps([serialize_cv2_keypoint(x) for x in key_points])
        descriptor_blob = pickle.dumps(descriptor)
        csr.execute("insert into image_sift_descriptor(image_key, key_points, descriptors) values (?, ?, ?)",
                    (key, key_point_blob, descriptor_blob))
    csr.close()
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
