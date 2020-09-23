__all__ = ['sift_class']


# noinspection PyUnresolvedReferences
def opencv_contrib_check():
    from logging import root
    sift = None
    try:
        import cv2
        opencv_version = cv2.__version__
        try:
            opencv_version_i = [int(x) for x in opencv_version.split('.')]
            if opencv_version_i[0] < 3 or (opencv_version_i[0] == 3 and opencv_version_i[1] < 4):
                root.warning('Detected OpenCV version: %s, this version is not tested yet, we recommend using OpenCV'
                             ' newer than 3.4' % opencv_version)
            else:
                root.info('Detected OpenCV version: %s' % opencv_version)
        except ValueError:
            root.info('Detected OpenCV version: %s' % opencv_version)
        try:
            try:
                sift = cv2.SIFT
            except AttributeError:
                sift = cv2.xfeatures2d_SIFT
        except (cv2.error, AttributeError):
            root.warning('SIFT algorithm is not support for current build of OpenCV, please rebuild using latest'
                         ' release')
    except ImportError:
        root.warning('OpenCV is not installed')
    return sift


sift_class = opencv_contrib_check()
