__all__ = ['sift_class']


# noinspection PyUnresolvedReferences
def opencv_contrib_check():
    import logging
    logger = logging.getLogger('bgo_script.image_process')
    sift = None
    try:
        import cv2
        opencv_version = cv2.__version__
        try:
            opencv_version_i = [int(x) for x in opencv_version.split('.')]
            if opencv_version_i[0] < 3 or (opencv_version_i[0] == 3 and opencv_version_i[1] < 4):
                logger.warning('Detected OpenCV version: %s, this version is not tested yet, we recommend using OpenCV'
                               ' newer than 3.4' % opencv_version)
            else:
                logger.info('Detected OpenCV version: %s' % opencv_version)
        except ValueError:
            logger.warning('Detected OpenCV version: %s (Failed to parse current build version)' % opencv_version)
        try:
            try:
                sift = cv2.SIFT
            except AttributeError:
                sift = cv2.xfeatures2d_SIFT
        except (cv2.error, AttributeError) as ex:
            logger.warning('SIFT algorithm is not support for current build of OpenCV, please rebuild using latest'
                           ' release', exc_info=ex)
    except ImportError:
        logger.warning('OpenCV is not installed')
    return sift


sift_class = opencv_contrib_check()
