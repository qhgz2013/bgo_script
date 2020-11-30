from _logging_config import script_logger_root
from attacher import MumuAttacher, AdbAttacher
from fsm import FgoFSMFacade, FgoFSMFacadeSelectSupport, FgoFSMFacadeBattleLoop
import argparse
import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('attacher', help='Attacher type', choices=['adb', 'mumu'], default='mumu', type=str, nargs='?')
    parser.add_argument('--schemas', help='Script execution schemas, one of "full" (from enter quest to exit quest),'
                                          '"support" (only perform support servant selection), or "battle" (only '
                                          'perform in-battle control)',
                        choices=['full', 'support', 'battle'], default='full', required=False)
    parser.add_argument('--verbose', help='Print verbose log (debug level) to screen', action='store_true',
                        default=False)
    args = parser.parse_args()
    attacher_dict = {'adb': AdbAttacher, 'mumu': MumuAttacher}
    schemas_dict = {'full': FgoFSMFacade, 'support': FgoFSMFacadeSelectSupport, 'battle': FgoFSMFacadeBattleLoop}
    attacher_class = attacher_dict.get(args.attacher.lower(), None)
    schemas_class = schemas_dict.get(args.schemas.lower(), None)
    if attacher_class is None:
        script_logger_root.critical('Unable to find attacher "%s"' % args.attacher)
        exit(1)
    if schemas_class is None:
        script_logger_root.critical('Unable to find execution schemas "%s"' % args.schemas)
        exit(1)
    script_logger_root.info('Using attacher class: %s' % str(attacher_class))
    script_logger_root.info('Using execution schemas: %s' % str(schemas_class))
    script = schemas_class(attacher_class(), config.DEFAULT_CONFIG)
    try:
        script.run()
    except Exception as ex:
        ex_type = type(ex)
        script_logger_root.critical(f'Exception while executing script: ({ex_type.__module__}.{ex_type.__qualname__}) '
                                    f'"{str(ex)}"', exc_info=ex, stack_info=True)


if __name__ == '__main__':
    main()
