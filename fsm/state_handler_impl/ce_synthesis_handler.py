from ..fgo_state import FgoState
from ..state_handler import StateHandler, WaitFufuStateHandler
from bgo_game import ScriptEnv
import image_process
from logging import getLogger
from time import sleep
import numpy as np
import sqlite3
from typing import *
from dataclasses import dataclass
from PIL import Image
from io import BytesIO
import json
from basic_class import Rect
import matplotlib.pyplot as plt
from time import time

__all__ = ['CraftEssenceSynthesisHandler']

logger = getLogger('bgo_script.fsm')
show_plot = False


@dataclass
class CEDetectionResult:
    id: int
    bounding_box: Rect
    flag: str  # lookup from Atlas database
    rarity: int  # lookup from Atlas database
    # currently there are 5 flags provided by Atlas database:
    # "normal", "svtEquipChocolate", "svtEquipFriendShip", "matDropRateUpCe", "svtEquipExp"
    available: bool
    locked: bool
    favored: bool  # not implemented yet


# TODO: move to util package?
def _bool_traversal(bool_list: np.ndarray, valid_bool_value: bool, start: int, max_lookahead_pixel: int = 0) -> int:
    # find the first index of bool_list that could not satisfy valid_bool_value
    y = start
    while y < len(bool_list):
        while y < len(bool_list) and bool_list[y] == valid_bool_value:
            y += 1
        if y == len(bool_list) or max_lookahead_pixel == 0:
            return y
        # met first invalid bool value
        lookahead_offset = 1
        while lookahead_offset <= max_lookahead_pixel and y + lookahead_offset < len(bool_list) \
                and bool_list[y + lookahead_offset] != valid_bool_value:
            lookahead_offset += 1
        if y == len(bool_list) or lookahead_offset > max_lookahead_pixel:
            return y
        else:
            y += lookahead_offset
    return y


class CraftEssenceSynthesisHandler(StateHandler):
    """Craft Essence Synthesis Handler: auto making craft essence with the following predefined rules:

    1. CE to be synthesized must be < 3 stars.
    2. Synthesis materials are all CEs with <= 3 stars (unlocked, and not favored), EXP CEs with 4 stars.

    The handler will perform a series of actions:

    - Click to select target CE.
    - Run filter check for selection UI (order by rarity, ascending, disable smart filtering and prioritizing).
    - Choose one CE that satisfies Rule 1.
    - Click to select materials.
    - Run filter check for selection UI (order by rarity, ascending, disable smart filtering and prioritizing).
    - Choose all CEs that satisfies Rule 2.
    - Perform synthesis and go back to step 4 until no more CE can be selected.

    """
    # HSV value, [3, 3], masked color: Brightness = origin value * 0.4
    anchor_color = np.array([[23, 210, 220],  # gold, verified H and S channels
                             [0, 0, 178],  # silver
                             [20, 97, 127],  # bronze
                             ], dtype=np.int32)
    _ui_size_img = None
    _synthesis_result_img = None
    _target_empty_img = None

    def __init__(self, env: ScriptEnv, forward_state: FgoState,
                 target_ce_not_found_forward_state: Optional[FgoState] = None):
        super(CraftEssenceSynthesisHandler, self).__init__(env, forward_state)
        cls = type(self)
        if cls._ui_size_img is None:
            cls._ui_size_img = image_process.imread(
                self.env.detection_definitions.get_craft_essence_material_ui_size_file())
        if cls._synthesis_result_img is None:
            # changed: rescale according to the ratio of height
            synthesis_result_img = image_process.imread(
                self.env.detection_definitions.get_craft_essence_synthesis_result_ui_file())
            resolution = self.env.detection_definitions.get_target_resolution()
            ratio = resolution.height / synthesis_result_img.shape[0]
            width = int(synthesis_result_img.shape[1] * ratio)
            cls._synthesis_result_img = image_process.resize(synthesis_result_img, width, resolution.height)
        if cls._target_empty_img is None:
            cls._target_empty_img = image_process.imread(
                self.env.detection_definitions.get_craft_essence_target_empty_file())
        self._target_filter_checked = False
        self._material_filter_checked = False
        self._sql_conn = sqlite3.connect(self.env.detection_definitions.get_database_file())
        self._sql_cursor = self._sql_conn.cursor()
        self._cache = image_process.ImageHashCacher(hash_func=image_process.perception_hash,
                                                    hash_conflict_func=image_process.mean_gray_diff_err)
        self._sql_cursor.execute("select ce_id from craft_essence_meta")
        self._ce_ids = [x[0] for x in self._sql_cursor.fetchall()]
        logger.debug(f'Craft essences in database: {len(self._ce_ids)}')
        self._img_cache = {}
        self._target_ce_not_found_forward_state = target_ce_not_found_forward_state or forward_state

    def _get_ce_image(self, ce_id: int, target_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        self._sql_cursor.execute("select image_key from craft_essence_faces where ce_id = ?", (ce_id,))
        image_key = self._sql_cursor.fetchone()
        if image_key is None:
            raise KeyError(f'Craft Essence ID "{ce_id}" not exists')
        image_key = image_key[0]
        self._sql_cursor.execute("select image_data from image where image_key = ?", (image_key,))
        data = self._sql_cursor.fetchone()
        if data is None:
            raise KeyError(f'Image "{image_key}" not exists')
        # TODO: change to use image_process package
        stream = BytesIO(data[0])
        pil_img = Image.open(stream)
        if target_size is not None:
            pil_img = pil_img.resize(target_size)
        # noinspection PyTypeChecker
        return np.asarray(pil_img, dtype=np.uint8)

    def _check_synthesis_ui_size(self):
        ui_size_rect = self.env.detection_definitions.get_craft_essence_material_ui_size_rect()
        logger.debug('Checking synthesis craft essence ui size')
        while True:
            img = self._get_screenshot_impl()
            img = img[ui_size_rect.y1:ui_size_rect.y2, ui_size_rect.x1:ui_size_rect.x2, :]
            diff = image_process.mean_gray_diff_err(img, self._ui_size_img)

            logger.debug(diff)
            if diff <= self.env.detection_definitions.get_craft_essence_ui_size_diff_threshold():
                break

            change_ui_size_click_pos = self.env.click_definitions.craft_essence_change_ui_size()
            self.env.attacher.send_click(change_ui_size_click_pos.x, change_ui_size_click_pos.y)
            sleep(1)
        logger.debug('Check finished')

    def _check_filter(self, smart_filtering: bool = False):
        logger.info('Running filter check')
        # only check once during the script time life
        target_filter_click_pos = self.env.click_definitions.craft_essence_synthesis_filter()
        self.env.attacher.send_click(target_filter_click_pos.x, target_filter_click_pos.y)
        sleep(1)

        img = self._get_screenshot_impl()

        # step 1: make sure target filter is ordered by rarity (ascending) TODO: custom order option?
        rect = self.env.detection_definitions.get_craft_essence_order_by_rarity_rect()
        img_in_rect = img[rect.y1:rect.y2, rect.x1:rect.x2, :]
        img_bin = img_in_rect[..., 0] >= \
            self.env.detection_definitions.get_craft_essence_order_by_rarity_r_threshold()
        ratio = np.mean(img_bin)
        filter_apply_click_pos = self.env.click_definitions.craft_essence_filter_cancel()

        if ratio < self.env.detection_definitions.get_craft_essence_order_by_rarity_r_ratio_threshold():
            logger.info('Filter updated: order by rarity')
            # update filter: order by rarity
            click_pos = self.env.click_definitions.craft_essence_order_by_rarity()
            self.env.attacher.send_click(click_pos.x, click_pos.y)
            sleep(0.5)
            # apply filter
            filter_apply_click_pos = self.env.click_definitions.craft_essence_filter_apply()

        # step 2: disable smart filter
        rect = self.env.detection_definitions.get_craft_essence_smart_filter_rect()
        img_in_rect = img[rect.y1:rect.y2, rect.x1:rect.x2, :]
        img_bin = img_in_rect[..., 2] >= \
            self.env.detection_definitions.get_craft_essence_extra_filter_b_threshold()
        ratio = np.mean(img_bin)
        logger.debug(f'smart filtering ratio: {ratio}')
        smart_filtering_enabled = \
            ratio >= self.env.detection_definitions.get_craft_essence_extra_filter_b_ratio_threshold()
        if smart_filtering_enabled != smart_filtering:
            logger.info('Filter updated: toggle smart filter')
            click_pos = self.env.click_definitions.craft_essence_toggle_smart_filter()
            self.env.attacher.send_click(click_pos.x, click_pos.y)
            sleep(0.5)
            filter_apply_click_pos = self.env.click_definitions.craft_essence_filter_apply()

        # step 3: disable selective filter
        rect = self.env.detection_definitions.get_craft_essence_selective_filter_rect()
        img_in_rect = img[rect.y1:rect.y2, rect.x1:rect.x2, :]
        img_bin = img_in_rect[..., 2] >= \
            self.env.detection_definitions.get_craft_essence_extra_filter_b_threshold()
        ratio = np.mean(img_bin)
        logger.debug(f'selective filtering ratio: {ratio}')
        if ratio >= self.env.detection_definitions.get_craft_essence_extra_filter_b_ratio_threshold():
            logger.info('Filter updated: toggle selective filter')
            click_pos = self.env.click_definitions.craft_essence_toggle_selective_filter()
            self.env.attacher.send_click(click_pos.x, click_pos.y)
            sleep(0.5)
            filter_apply_click_pos = self.env.click_definitions.craft_essence_filter_apply()

        self.env.attacher.send_click(filter_apply_click_pos.x, filter_apply_click_pos.y)
        sleep(1)

        # check ascending or descending order
        order_rect = self.env.detection_definitions.get_craft_essence_order_ascending_rect()
        img_in_rect = np.mean(img[order_rect.y1:order_rect.y2, order_rect.x1:order_rect.x2, :], axis=(1, 2))
        slope = np.polyfit(np.arange(len(img_in_rect)), img_in_rect, 1)[0]
        logger.debug(f'filter ascending / descending slope: {slope}')
        if slope < 0:
            logger.info('Filter updated: order by ascending')
            click_pos = self.env.click_definitions.craft_essence_toggle_order()
            self.env.attacher.send_click(click_pos.x, click_pos.y)
            sleep(1)

    def _detect_material_grid_y(self, img: Optional[np.ndarray] = None) -> List[Tuple[int, int]]:
        if img is None:
            img = self._get_screenshot_impl(precise_mode=True)
        img_hsv = image_process.rgb_to_hsv(img).astype(np.int32)

        x_begin, x_end = self.env.detection_definitions.get_craft_essence_material_x_range()
        margin_x = self.env.detection_definitions.get_craft_essence_material_margin_x()
        num_per_row = self.env.detection_definitions.get_craft_essence_n_materials_per_row()  # should be 7
        width = ((x_end - x_begin) - margin_x * (num_per_row - 1)) / num_per_row
        y_begin = self.env.detection_definitions.get_craft_essence_material_y_start()
        frame_detection_ratio = self.env.detection_definitions.get_craft_essence_frame_detection_ratio()  # 0.23

        x_splits = []  # record the x-axis for each column
        # 4d tensor: [n_anchors (3), n_rows (7), height, channel (3)]
        hsv_diff_tensor_shape = (self.anchor_color.shape[0], num_per_row, img.shape[0] - y_begin,
                                 self.anchor_color.shape[1])
        hsv_diff_tensor = np.empty(hsv_diff_tensor_shape, dtype=np.float32)
        for i in range(num_per_row):
            x1 = x_begin + i * (width + margin_x)
            x2 = x1 + width
            ix1, ix2 = int(round(x1)), int(round(x2))
            x_splits.append((ix1, ix2))

            # use first 23% and last 23% (the middle 54% is noise when craft essence is using) by default
            detection_ix1 = int(round(x1 + frame_detection_ratio * width))
            detection_ix2 = int(round(x2 - frame_detection_ratio * width))

            detection_hsv_img1 = img_hsv[y_begin:, ix1+2:detection_ix1]
            detection_hsv_img2 = img_hsv[y_begin:, detection_ix2:ix2-2]
            detection_hsv_img = np.concatenate([detection_hsv_img1, detection_hsv_img2], 1)  # [height, width, 3]

            # new: add std error among x axis
            std = np.std(detection_hsv_img, 1)  # [height, 3]

            for j, anchor_hsv in enumerate(self.anchor_color):
                anchor_hsv = np.expand_dims(anchor_hsv, [0, 1])  # [1, 1, channel (3)]
                diff = np.mean(np.abs(detection_hsv_img - anchor_hsv), 1)  # [height, 3]
                hsv_diff_tensor[j, i, :, :] = diff + std * 1.0  # weighted as 1.0?

        # choose minimized difference along anchor-axis
        hsv_diff_reduction_anchor = np.min(hsv_diff_tensor, 0)  # [n_rows (7), height, channel (3)]
        # mean pooling along different rows
        hsv_diff_reduction_row = np.mean(hsv_diff_reduction_anchor, 0)  # [height, channel (3)]
        # now we use H and S channel omitting V channel
        hsv_diff_reduction_row = hsv_diff_reduction_row[..., :2]  # [height, channel (2)]
        # mean pooling along channel axis
        hsv_diff_reduction_row = np.mean(hsv_diff_reduction_row, 1)  # [height]

        if show_plot:
            plt.figure()
            plt.plot(hsv_diff_reduction_row)
            plt.grid()
            plt.show()

            plt.figure()
            plt.plot(np.mean(hsv_diff_reduction_anchor[..., :2], -1).T)
            plt.grid()
            plt.legend([f'row_{i+1}' for i in range(num_per_row)], loc='upper left')
            plt.show()

        # configurable param
        tol_pixels = self.env.detection_definitions.get_craft_essence_grid_detection_tol_pixels()  # 3
        split_threshold = self.env.detection_definitions.get_craft_essence_grid_detection_hsv_threshold()  # 30
        height = self.env.detection_definitions.get_craft_essence_material_height()  # 128

        if show_plot:
            plt.figure()
            plt.plot(np.sum(np.mean(hsv_diff_reduction_anchor[..., :2], -1) < split_threshold, 0))
            plt.grid()
            plt.show()

        margin = self.env.detection_definitions.get_craft_essence_material_margin_y()  # 14
        guessed_available_cols = np.sum(np.mean(hsv_diff_reduction_anchor[..., :2], -1) < split_threshold, 0)
        # project to height+margin
        accumulated_values = np.zeros(height + margin, dtype=np.int32)
        for i in range(0, len(guessed_available_cols), height + margin):
            slice_values = guessed_available_cols[i:i + height + margin]
            accumulated_values[:len(slice_values)] += slice_values

        max_val = np.max(accumulated_values)
        threshold = max_val * self.env.detection_definitions.get_craft_essence_grid_detection_conf_threshold()  # 0.8
        # extend accumulated_values 2x
        accumulated_values = np.concatenate([accumulated_values, accumulated_values])
        if show_plot:
            plt.figure()
            plt.plot(accumulated_values)
            plt.grid()
            plt.show()

        split_flag = accumulated_values > threshold
        min_margin = self.env.detection_definitions.get_craft_essence_grid_detection_area_min_pixels()
        y = 0
        valid_y = None
        results = []
        while y < height + margin:  # 128+14=142
            y1 = _bool_traversal(split_flag, valid_bool_value=False, start=y, max_lookahead_pixel=tol_pixels)
            y = _bool_traversal(split_flag, valid_bool_value=True, start=y1, max_lookahead_pixel=tol_pixels)
            results.append(f'{y1}-{y} (length: {y-y1})')
            if margin > y - y1 >= min_margin:
                valid_y = (y1 + y) // 2
                break
        if valid_y is None:
            raise ValueError(f'Could not detect craft essence material grid, all results "{results}" are not in '
                             f'range: [{min_margin}, {margin})')
        # y = (valid_y + margin // 2) % (margin + height)  # bottom pixel
        y %= (margin + height)
        repeat_cnt = (guessed_available_cols.shape[0] - y) // (height + margin)
        y_coords = [((height + margin) * i - height + y, (height + margin) * i + y) for i in range(1, repeat_cnt+1)]
        logger.debug(y_coords)

        if show_plot:
            img2 = img.copy()
            for y1, y2 in y_coords:
                img2[y1 + y_begin, :, 0] = 255
                img2[y2 + y_begin, :, 1] = 255

            for i in range(num_per_row):
                x1 = x_begin + i * (width + margin_x)
                x2 = x1 + width
                ix1, ix2 = int(round(x1)), int(round(x2))
                img2[:, ix1, 0] = 255
                img2[:, ix2, 1] = 255

            plt.figure(figsize=(16, 9))
            plt.imshow(img2)
            plt.show()

        # add y_begin before returning, since we truncated the beginning position to y_begin before
        return [(a + y_begin, b + y_begin) for a, b in y_coords]

    def _ce_image_lookup(self, img: np.ndarray) -> Tuple[int, Dict[str, Any]]:
        cache_result = self._cache.get(img, None)
        # perf debug
        t0 = time()
        if cache_result is not None:
            return cache_result
        min_val = 0x7fffffff
        min_idx = -1
        # TODO: MP dispatch
        for ce in self._ce_ids:
            if ce not in self._img_cache:
                self._img_cache[ce] = self._get_ce_image(ce, (img.shape[1], img.shape[0]))
            val = image_process.mean_gray_diff_err(img, self._img_cache[ce])
            if val < min_val:
                min_val = val
                min_idx = ce
        self._sql_cursor.execute("select meta_json from craft_essence_meta where ce_id = ?", (min_idx,))
        meta_json = self._sql_cursor.fetchone()[0]
        meta = json.loads(meta_json)
        self._cache[img] = min_idx, meta
        logger.debug(f'ce lookup time: {time() - t0:.3f}s, result: {min_idx} ({meta["original_name"]})')
        return min_idx, meta

    def _detect_material_grid(self, y_loc: Optional[List[Tuple[int, int]]] = None,
                              img: Optional[np.ndarray] = None) -> List[List[CEDetectionResult]]:
        if img is None:
            img = self._get_screenshot_impl(precise_mode=True)
        if y_loc is None:
            y_loc = self._detect_material_grid_y(img)

        # compute x_begin and x_end for each column
        x_begin, x_end = self.env.detection_definitions.get_craft_essence_material_x_range()
        x_margin = self.env.detection_definitions.get_craft_essence_material_margin_x()
        num_per_row = self.env.detection_definitions.get_craft_essence_n_materials_per_row()  # should be 7
        width = ((x_end - x_begin) - x_margin * (num_per_row - 1)) / num_per_row
        width_round = int(round(width))  # preventing varying width
        x_loc = []
        for i in range(num_per_row):
            x1 = int(round((width + x_margin) * i + x_begin))
            x2 = x1 + width_round
            x_loc.append((x1, x2))

        inner_rect = self.env.detection_definitions.get_craft_essence_material_inner_image_rect()
        frame_detection_ratio = self.env.detection_definitions.get_craft_essence_frame_detection_ratio()  # 0.23
        unavailable_threshold = self.env.detection_definitions.get_craft_essence_unavailable_v_threshold()  # 0.5
        rescale_ratio = self.env.detection_definitions.get_craft_essence_unavailable_v_rescale_ratio()  # 0.4
        empty_slot_threshold = self.env.detection_definitions.get_craft_essence_empty_slot_h_diff_threshold()  # 20
        lock_y1, lock_y2 = self.env.detection_definitions.get_craft_essence_lock_detection_y_range()
        lock_std_threshold = self.env.detection_definitions.get_craft_essence_lock_std_threshold()
        if inner_rect.width != inner_rect.height:
            raise ValueError(f'get_craft_essence_material_inner_image_rect must return a square rect,'
                             f' but got: {inner_rect!r}')

        ce_grid = []
        for i, (y1, y2) in enumerate(y_loc):
            row = []
            for j, (x1, x2) in enumerate(x_loc):
                cell_img = img[y1:y2, x1:x2, :]
                # detect black overlay (unavailable status)
                cell_img_hsv = image_process.rgb_to_hsv(cell_img)
                # use first 23% and last 23% (the middle 54% is noise when craft essence is using) by default
                detection_x = int(round(frame_detection_ratio * width))
                frame_bottom = np.concatenate([cell_img_hsv[inner_rect.y2:, :detection_x],
                                               cell_img_hsv[inner_rect.y2:, -detection_x:]], axis=1)
                ce_frame_type_hsv = np.expand_dims(np.mean(frame_bottom, axis=(0, 1)), axis=0)  # [1, 3]
                diff = np.abs(ce_frame_type_hsv - self.anchor_color)  # [n, 3]
                if np.min(diff[:, 0]) > empty_slot_threshold:
                    # empty slot
                    logger.debug(f'empty slot detected at x: {x1}-{x2}, y: {y1}-{y2} (x: {j}, y: {i} in grid)')
                    continue
                anchor_idx = np.argmin(np.sum(diff[:, :2], axis=1))
                # normally it is ~0.6, set to 0.5 here
                ce_unavailable = (diff[anchor_idx, 2] / self.anchor_color[anchor_idx, 2]) > unavailable_threshold
                if ce_unavailable:
                    # rescale V channel
                    cell_img_hsv_rescale = cell_img_hsv.astype(np.float32)
                    cell_img_hsv_rescale[..., 2] /= rescale_ratio
                    cell_img_hsv_rescale = np.clip(cell_img_hsv_rescale, 0, 255).astype(np.uint8)
                    cell_img = image_process.hsv_to_rgb(cell_img_hsv_rescale)

                if show_plot:
                    # plot
                    plt.figure()
                    plt.imshow(cell_img)
                    plt.show()

                # lock detection
                lock_img = cell_img[lock_y1:lock_y2, :inner_rect.x1, :]
                std = np.mean(np.std(np.mean(lock_img, axis=2), axis=0))  # locked >= 71, unlock <= 25
                # logger.debug(f'lock detection std: {std}')
                locked = std > lock_std_threshold

                cell_img_inner = cell_img[inner_rect.y1:inner_rect.y2, inner_rect.x1:inner_rect.x2, :]
                ce_id, ce_meta = self._ce_image_lookup(cell_img_inner)
                ce_flag = ce_meta['flag']
                ce_rarity = ce_meta['rarity']
                result = CEDetectionResult(ce_id, flag=ce_flag, available=not ce_unavailable, locked=locked,
                                           favored=False, rarity=ce_rarity, bounding_box=Rect(x1, y1, x2, y2))
                row.append(result)
                logger.debug(repr(result))
            ce_grid.append(row)
        return ce_grid

    def _select_ce(self, ce_bounding_box: Rect):
        resolution = self.env.detection_definitions.get_target_resolution()
        # compute central point and normalize
        x = int(round((ce_bounding_box.x1 + ce_bounding_box.x2) / 2)) / resolution.width
        y = int(round((ce_bounding_box.y1 + ce_bounding_box.y2) / 2)) / resolution.height
        self.env.attacher.send_click(x, y)

    def _lock_ce(self, ce_bounding_box: Rect):
        toggle_lock = self.env.click_definitions.craft_essence_toggle_lock()
        self.env.attacher.send_click(toggle_lock.x, toggle_lock.y)
        sleep(1)
        self._select_ce(ce_bounding_box)
        sleep(1)
        toggle_ce = self.env.click_definitions.craft_essence_toggle_ce_selection()
        self.env.attacher.send_click(toggle_ce.x, toggle_ce.y)
        sleep(1)
        # this will make a request, so we need to wait for the response
        WaitFufuStateHandler(self.env, FgoState.STATE_FINISH).run_and_transit_state()

    def _select_target_ce(self, ce_grid_data: List[List[CEDetectionResult]]) -> bool:
        for row in ce_grid_data:
            for cell in row:
                if cell.available and cell.rarity < 3:
                    if not cell.locked:
                        self._lock_ce(cell.bounding_box)
                    self._select_ce(cell.bounding_box)
                    sleep(1)
                    return True
        return False

    def _select_material_ce(self, ce_grid_data: List[List[CEDetectionResult]]) -> int:
        selected_ce_count = 0
        for row in ce_grid_data:
            for cell in row:
                if cell.available and not cell.locked and not cell.favored and \
                        (cell.rarity <= 3 or cell.flag == 'svtEquipExp'):
                    self._select_ce(cell.bounding_box)
                    sleep(0.2)
                    selected_ce_count += 1
                # stop when 20 materials are selected
                if selected_ce_count >= 20:
                    break
            if selected_ce_count >= 20:
                break
        if selected_ce_count > 0:
            confirm = self.env.click_definitions.craft_essence_confirm()
            self.env.attacher.send_click(confirm.x, confirm.y)
        else:
            cancel = self.env.click_definitions.synthesis_cancel()
            self.env.attacher.send_click(cancel.x, cancel.y)
        sleep(1)
        logger.info(f'Selected {selected_ce_count} materials')
        return selected_ce_count

    def _wait_synthesis_complete(self):
        click_pos = self.env.click_definitions.craft_essence_confirm()  # use confirm button here
        threshold = self.env.detection_definitions.get_craft_essence_wait_synthesis_complete_diff_threshold()
        max_wait_seconds = 10
        t = time()
        while True:
            img = self._get_screenshot_impl()
            x = (img.shape[1] - self._synthesis_result_img.shape[1]) // 2
            img = img[:, x:x+self._synthesis_result_img.shape[1], :]
            diff = image_process.mean_gray_diff_err(img, self._synthesis_result_img)
            logger.debug(f'_wait_synthesis_complete diff: {diff}, threshold: {threshold}')
            if diff < threshold:
                break
            self.env.attacher.send_click(click_pos.x, click_pos.y)
            sleep(0.5)
            if time() - t > max_wait_seconds:
                # sometimes the click action will affect the detection result, we need to set a timeout
                logger.warning(f'Wait synthesis complete timeout: {max_wait_seconds} seconds, '
                               f'skip waiting and continue')
                break
        sleep(0.5)  # 1.5  animation delay
        # todo: check state before exit
        for _ in range(3):  # multiple clicks are required to prevent failure
            self.env.attacher.send_click(click_pos.x, click_pos.y)
            sleep(0.5)

    def _target_ce_presence(self) -> bool:
        rect = self.env.detection_definitions.get_craft_essence_target_rect()
        img = self._get_screenshot_impl()
        img = img[rect.y1:rect.y2, rect.x1:rect.x2, :]
        diff = image_process.mean_gray_diff_err(img, self._target_empty_img)
        logger.debug(f'_target_ce_presence diff: {diff}')
        return diff > self.env.detection_definitions.get_craft_essence_target_empty_diff_threshold()

    def run_and_transit_state(self) -> FgoState:
        # synthesis loop
        while True:
            # step 0: check target CE presence
            if not self._target_ce_presence():

                # step 1: enter target selection UI
                logger.info('Select target craft essence')
                target_ce_click_pos = self.env.click_definitions.craft_essence_synthesis_target_select()
                self.env.attacher.send_click(target_ce_click_pos.x, target_ce_click_pos.y)

                sleep(2)

                # step 2: check UI size
                self._check_synthesis_ui_size()

                # step 3: check target filter
                if not self._target_filter_checked:
                    self._check_filter()
                    self._target_filter_checked = True

                # step 4: detect material grid
                ce_data = self._detect_material_grid()

                # step 5: select target CE
                if not self._select_target_ce(ce_data):
                    logger.info('No target CE found, skip synthesis')
                    cancel = self.env.click_definitions.synthesis_cancel()
                    self.env.attacher.send_click(cancel.x, cancel.y)
                    sleep(1)
                    return self._target_ce_not_found_forward_state

            # step 6: enter material selection UI
            material_ce_click_pos = self.env.click_definitions.craft_essence_synthesis_material_select()
            self.env.attacher.send_click(material_ce_click_pos.x, material_ce_click_pos.y)

            sleep(2)

            # step 7: check UI size (can be opted out for the second time)
            self._check_synthesis_ui_size()

            # step 8: check material filter
            if not self._material_filter_checked:
                self._check_filter(smart_filtering=True)
                self._material_filter_checked = True

            # step 9: detect material grid
            ce_data = self._detect_material_grid()

            # step 10: select material CE
            selected_ce_count = self._select_material_ce(ce_data)
            if selected_ce_count == 0:
                logger.info('No material CE found, skip synthesis')
                break

            # step 11: synthesis
            confirm = self.env.click_definitions.craft_essence_confirm()
            self.env.attacher.send_click(confirm.x, confirm.y)
            sleep(0.5)
            # double confirm
            double_confirm = self.env.click_definitions.craft_essence_double_confirm_yes()
            self.env.attacher.send_click(double_confirm.x, double_confirm.y)
            sleep(2)
            # wait complete
            self._wait_synthesis_complete()

        return self.forward_state
