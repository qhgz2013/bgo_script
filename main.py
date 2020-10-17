from _logging_config import script_logger_root
from attacher import MumuAttacher, AdbAttacher
from fsm import FgoFSMFacade, FgoFSMFacadeSelectSupport
import argparse
import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('attacher', help='Attacher type', choices=['adb', 'mumu'], default='mumu', type=str, nargs='?')
    parser.add_argument('--schemas', help='Script execution schemas, one of "full" (from enter quest to exit quest),'
                                          ' or "support" (only perform support servant selection)',
                        choices=['full', 'support'], default='full', required=False)
    args = parser.parse_args()
    attacher_dict = {'adb': AdbAttacher, 'mumu': MumuAttacher}
    schemas_dict = {'full': FgoFSMFacade, 'support': FgoFSMFacadeSelectSupport}
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
        script_logger_root.critical('Exception while executing script: %s' % str(ex), exc_info=ex, stack_info=True)


if __name__ == '__main__':
    main()
