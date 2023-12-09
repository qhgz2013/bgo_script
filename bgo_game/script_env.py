from util import SingletonMeta
from ._class_def import BattleController, TeamConfig, APRecoveryItemType
from attacher import AntiDetectionConfig, AttacherRegistry, CapturerRegistry, AntiDetectionAttacher
from typing import *
from logging import getLogger
from resolution_adapter import DetectionDefFactory, ClickDefFactory
import importlib
from attacher import AttacherBase, ScreenCapturer
from .compact_option import CompactOption

__all__ = ['ScriptEnv']

logger = getLogger('bgo_script.script_env')


class ScriptEnv(metaclass=SingletonMeta):
    """A singleton class holding the runtime variables for executing the whole automation script."""

    def __init__(self, attacher: Union[str, AttacherBase], capturer: [str, ScreenCapturer],
                 controller: Union[str, Type[BattleController]], team_config: [str, TeamConfig],
                 anti_detection_cfg: Optional[AntiDetectionConfig] = None,
                 ap_recovery_item_type: APRecoveryItemType = APRecoveryItemType.DontEatMyApple,
                 enable_continuous_battle: bool = True,
                 *, controller_import: str = 'config', team_config_import: str = 'config',
                 laplace_team_data_cache_dir: str = 'laplace_cache',
                 compact_option: Optional[CompactOption] = None):
        if isinstance(attacher, str):
            logger.info(f'Instantiating attacher {attacher}')
            attacher_cls = AttacherRegistry.get_handler(attacher)
            if attacher_cls is None:
                raise ValueError(f'Could not get attacher for name {attacher}, available names are '
                                 f'{AttacherRegistry.get_all_handler_names()}')
            self.attacher = attacher_cls()  # type: AttacherBase
        else:
            assert isinstance(self.attacher, AttacherBase),\
                f'attacher must be either a string or an AttacherBase, got {type(attacher)!r}'
            self.attacher = attacher
        logger.info(f'Using attacher: {self.attacher!r}')

        if isinstance(capturer, str):
            logger.info(f'Instantiating capturer {capturer}')
            capturer_cls = CapturerRegistry.get_handler(capturer)
            if capturer_cls is None:
                raise ValueError(f'Could not get capturer for name {capturer}, available names are '
                                 f'{CapturerRegistry.get_all_handler_names()}')
            self.capturer = capturer_cls()  # type: ScreenCapturer
        else:
            assert isinstance(self.capturer, ScreenCapturer),\
                f'capturer must be either a string or a ScreenCapturer, got {type(capturer)!r}'
            self.capturer = capturer
        logger.info(f'Using capturer: {self.capturer!r}')

        if isinstance(controller, str):
            try:
                self.controller_cls = getattr(importlib.import_module(controller_import), controller)
            except AttributeError:
                raise ValueError(f'Could not find controller class {controller} from controller import file '
                                 f'{controller_import}')
        else:
            self.controller_cls = controller
        assert issubclass(self.controller_cls, BattleController),\
            f'controller must be either a string or a BattleController class, got {self.controller_cls!r}'
        logger.info(f'Using controller: {self.controller_cls!r}')

        if isinstance(team_config, str):
            try:
                self.team_config = getattr(importlib.import_module(team_config_import), team_config)
            except AttributeError:
                raise ValueError(f'Could not find team config {team_config} from team config import file '
                                 f'{team_config_import}')
        else:
            self.team_config = team_config
        assert isinstance(self.team_config, TeamConfig),\
            f'team_config must be either a string or a TeamConfig, got {type(team_config)!r}'
        logger.info(f'Using team config: {self.team_config!r}')

        self.anti_detection_cfg = anti_detection_cfg
        if anti_detection_cfg is not None:
            logger.info(f'Using anti-detection config: {anti_detection_cfg}')
            self.attacher = AntiDetectionAttacher(self.attacher, anti_detection_cfg)

        resolution = self.capturer.get_resolution()
        logger.info(f'Capturer resolution: {resolution}')
        self.click_definitions = ClickDefFactory.get_click_def(resolution)
        logger.info(f'Using click definition: {self.click_definitions!r}')
        self.detection_definitions = DetectionDefFactory.get_detection_def(resolution)
        logger.info(f'Using detection definition: {self.detection_definitions!r}')

        self.runtime_var_store = {}
        self.ap_recovery_item_type = ap_recovery_item_type
        self.enable_continuous_battle = enable_continuous_battle
        self.laplace_team_data_cache_dir = laplace_team_data_cache_dir
        if compact_option is None:
            compact_option = CompactOption()
        self.compact_option = compact_option
        self.detection_definitions.compact_option = compact_option
