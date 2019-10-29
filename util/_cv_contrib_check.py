# noinspection PyUnresolvedReferences
def opencv_contrib_check():
    from warnings import warn
    try:
        import cv2
        opencv_version = cv2.__version__
        if not opencv_version.startswith('3.4'):
            warn('Detected current OpenCV version: %s. This version is not tested, '
                 'we recommends OpenCV later than 3.4.' % opencv_version)
        else:
            print('Detected OpenCV version: %s' % opencv_version)
        try:
            cv2.xfeatures2d_SIFT.create()
        except cv2.error:
            warn('SIFT algorithm is not support for current build of OpenCV, please rebuild with contrib module and'
                 'enable OPENCV_ENABLE_NONFREE')
    except ImportError:
        warn('OpenCV is not installed')


opencv_contrib_check()
