import logging

logger = logging.getLogger('bgo_script.image_process.benchmark')


def run_all_benchmark():
    logger.info('Running gaussian blur benchmark')
    from .gauss_blur import benchmark as a
    a()
    logger.info('Running imdecode benchmark')
    from .imdecode import benchmark as b
    b()
    logger.info('Running imread benchmark')
    from .imread import benchmark as c
    c()
    logger.info('Running resize benchmark')
    from .resize import benchmark as d
    d()
    logger.info('Running rgb hsv benchmark')
    from .rgb_hsv import benchmark as e
    e()
