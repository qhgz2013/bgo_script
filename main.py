import _logging_config
from attacher import *
from fsm import *
import argparse
import config
import logging

script_logger_root = logging.getLogger('bgo_script')


def _log_exception(ex: BaseException):
    ex_type = type(ex)
    script_logger_root.critical(f'Exception while executing script: ({ex_type.__module__}.{ex_type.__qualname__}) '
                                f'"{str(ex)}"', exc_info=ex, stack_info=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('attacher', help='Attacher type', choices=['adb', 'mumu', 'mumu_root', 'adb_root'],
                        default='mumu_root', type=str, nargs='?')
    parser.add_argument('--capturer', help='Capturer type', choices=['adb', 'adb_native', 'mumu', 'default'],
                        default='default', type=str)
    parser.add_argument('--schemas', help='Script execution schemas, one of "full" (from enter quest to exit quest),'
                                          '"support" (only perform support servant selection), or "battle" (only '
                                          'perform in-battle control)',
                        choices=['full', 'support', 'battle'], default='full', required=False)
    parser.add_argument('--verbose', help='Print verbose log (debug level) to screen', action='store_true',
                        default=False)
    args = parser.parse_args()
    _logging_config.bootstrap(log_to_screen_loggers={None: logging.WARNING, 'bgo_script': None},
                              write_to_file_loggers={None: logging.INFO, 'bgo_script': logging.DEBUG},
                              default_log_to_screen_level=logging.DEBUG if args.verbose else logging.INFO,
                              file_name_prefix='bgo_script')
    attacher_dict = {'adb': ADBAttacher, 'mumu': MumuAttacher, 'mumu_root': MumuRootAttacher,
                     'adb_root': ADBRootAttacher}
    default_capturer_dict = {'adb': ADBScreenrecordCapturer, 'adb_root': ADBScreenrecordCapturer,
                             'mumu': MumuScreenCapturer, 'mumu_root': MumuScreenCapturer}
    capturer_dict = {'adb': ADBScreenrecordCapturer, 'mumu': MumuScreenCapturer, 'adb_native': ADBScreenCapturer}
    schemas_dict = {'full': FgoFSMFacade, 'support': FgoFSMFacadeSelectSupport, 'battle': FgoFSMFacadeBattleLoop}
    attacher_class = attacher_dict.get(args.attacher.lower(), None)
    schemas_class = schemas_dict.get(args.schemas.lower(), None)
    capturer = args.capturer.lower()
    capturer_class = default_capturer_dict.get(args.attacher, None) if capturer == 'default' \
        else capturer_dict.get(capturer, None)
    if attacher_class is None:
        script_logger_root.critical(f'Unable to find attacher "{args.attacher}"')
        exit(1)
    if schemas_class is None:
        script_logger_root.critical(f'Unable to find execution schemas "{args.schemas}"')
        exit(1)
    if capturer_class is None:
        script_logger_root.critical(f'Unable to find capturer "{capturer}"')
        exit(1)
    script_logger_root.info(f'Using attacher class: {attacher_class!r}')
    script_logger_root.info(f'Using execution schemas: {schemas_class!r}')
    script_logger_root.info(f'Using capturer: {capturer_class!r}')
    try:
        script = schemas_class(CombinedAttacher(capturer_class(), attacher_class()), config.DEFAULT_CONFIG)
        script.run_and_transit_state()
    except KeyboardInterrupt as kb_int:
        script_logger_root.info('Keyboard interrupted')
        _log_exception(kb_int)
        raise kb_int
    except Exception as ex:
        _log_exception(ex)


if __name__ == '__main__':
    main()
