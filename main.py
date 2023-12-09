import _logging_config
from bgo_game import ScriptEnv, APRecoveryItemType, CompactOption
import argparse
import logging
from attacher import AntiDetectionConfig
from fsm import FgoFSMFacadeFactory

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
                                          'perform in-battle control), "friend_point"',
                        choices=['full', 'support', 'battle', 'friend_point'], default='full', required=False)
    parser.add_argument('--controller', help='Class name of BattleController in use (defined in config.py)',
                        default='DEFAULT_CONTROLLER')
    parser.add_argument('--team_config', help='Variable name of TeamConfig in use (defined in config.py)',
                        default='DEFAULT_TEAM_CONFIG')
    parser.add_argument('--enable_anti_detection', action='store_true', help='Enable anti-detection mechanism')
    parser.add_argument('--ap_recovery', default='no', help='Enable AP auto recovery by using specified items',
                        choices=['no', 'gold', 'silver', 'bronze', 'saint_quartz', 'sapling'])
    parser.add_argument('--notify_at_exit', action='store_true', help='Notify user at script exit')
    parser.add_argument('--compact_option', nargs='+', help='Compact options for CHS and JPN server')
    parser.add_argument('--verbose', help='Print verbose log (debug level) to screen', action='store_true',
                        default=False)
    args = parser.parse_args()
    _logging_config.bootstrap(log_to_screen_loggers={None: logging.WARNING, 'bgo_script': None},
                              write_to_file_loggers={None: logging.INFO, 'bgo_script': logging.DEBUG},
                              default_log_to_screen_level=logging.DEBUG if args.verbose else logging.INFO,
                              file_name_prefix='bgo_script')

    if args.capturer == 'default':
        args.capturer = 'adb' if 'adb' in args.attacher else 'mumu'

    anti_detection_cfg = AntiDetectionConfig(enable_random_offset=args.enable_anti_detection,
                                             enable_random_latency=args.enable_anti_detection)

    ap_recovery_item_type_dict = {'no': APRecoveryItemType.DontEatMyApple, 'gold': APRecoveryItemType.GoldApple,
                                  'silver': APRecoveryItemType.SilverApple, 'bronze': APRecoveryItemType.BronzeApple,
                                  'saint_quartz': APRecoveryItemType.SaintQuartz,
                                  'sapling': APRecoveryItemType.BronzeSapling}
    ap_recovery_item = ap_recovery_item_type_dict[args.ap_recovery]

    if len(args.compact_option) > 0:
        compact_kwargs = {opt: True for opt in args.compact_option}
        compact_opt = CompactOption(compact_kwargs)
    else:
        compact_opt = None
    script_env = ScriptEnv(args.attacher, args.capturer, args.controller, args.team_config, anti_detection_cfg,
                           ap_recovery_item, controller_import='config', team_config_import='config',
                           compact_option=compact_opt)
    schemas_class = FgoFSMFacadeFactory.get_handler(args.schemas)
    if schemas_class is None:
        raise ValueError(f'Invalid schemas: {args.schemas}')
    try:
        # noinspection PyArgumentList
        script = schemas_class(script_env)
        script.run_and_transit_state()
    except KeyboardInterrupt as kb_int:
        script_logger_root.info('Keyboard interrupted')
        _log_exception(kb_int)
        # raise kb_int
    except Exception as ex:
        _log_exception(ex)
    if args.notify_at_exit:
        from util import balloon_tip
        balloon_tip('bgo_script', 'Script exited')


if __name__ == '__main__':
    main()
