from _logging_config import script_logger_root
from attacher import MumuAttacher, AdbAttacher
from fsm import FgoFSMFacade
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('attacher', help='Attacher type', choices=['adb', 'mumu'], default='mumu', type=str, nargs='?')
    args = parser.parse_args()
    attacher_dict = {'adb': AdbAttacher, 'mumu': MumuAttacher}
    attacher_class = attacher_dict.get(args.attacher.lower(), None)
    if attacher_class is None:
        script_logger_root.critical('Unable to find attacher "%s"' % args.attacher)
    script_logger_root.info('Using attacher class: %s' % str(attacher_class))
    script = FgoFSMFacade(attacher_class())
    script.run()


if __name__ == '__main__':
    main()
