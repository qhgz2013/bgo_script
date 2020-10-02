from _logging_config import script_logger_root
from attacher import MumuAttacher, AdbAttacher
from fsm import FgoFSMFacade
import argparse


def get_cfg():
    from battle_control import ScriptConfiguration, EatAppleType, BattleController,TeamConfiguration,ServantConfiguration, SupportServantConfiguration
    class BC(BattleController):
        def __call__(self, *args, **kwargs):
            print(args)
            print(kwargs)
            self.attack(1).attack(2).attack(0)
    svts = [ServantConfiguration(1,2), ServantConfiguration(3,4), SupportServantConfiguration(0,1106), ServantConfiguration(7,8), ServantConfiguration(2,3), ServantConfiguration(4,5)]
    cfg = ScriptConfiguration(EatAppleType.DontEatMyApple, BC, TeamConfiguration(svts))
    return cfg

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('attacher', help='Attacher type', choices=['adb', 'mumu'], default='mumu', type=str, nargs='?')
    args = parser.parse_args()
    attacher_dict = {'adb': AdbAttacher, 'mumu': MumuAttacher}
    attacher_class = attacher_dict.get(args.attacher.lower(), None)
    if attacher_class is None:
        script_logger_root.critical('Unable to find attacher "%s"' % args.attacher)
    script_logger_root.info('Using attacher class: %s' % str(attacher_class))
    script = FgoFSMFacade(attacher_class(), get_cfg())
    script.run()


if __name__ == '__main__':
    main()
