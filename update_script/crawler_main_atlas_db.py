import requests
import sqlite3
from dataclasses import dataclass, asdict
from typing import *
import re
import importlib
import logging
import argparse
from time import time
import json
import os
from image_process import perception_hash
from io import BytesIO
from PIL import Image
import numpy as np

logger = None  # type: Optional[logging.Logger]


def configure_logging():
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s]'
                                                   ' (%(filename)s:%(lineno)d) %(message)s')
    global logger
    logger = logging.getLogger(__name__)


@dataclass
class ServantCostume:
    id: int
    costume_collection_no: int
    battle_chara_id: int
    short_name: str


@dataclass
class ServantMeta:
    atk_max: int
    attribute: str
    class_name: str
    class_id: int
    collection_no: int
    costume: Dict[str, ServantCostume]
    face: str  # url
    flag: str
    hp_max: int
    id: int
    name: str  # EN name
    original_name: str  # JP name
    rarity: int
    type: str
    overwrite_name: str = ''
    original_overwrite_name: str = ''


@dataclass
class ServantFigure:
    ascension: Optional[Dict[str, str]] = None  # key: 1-4 (str type), value: url (str type)


@dataclass
class ServantExtraAssets:
    # chara_figure: ServantFigure  # 剧情立绘，带差分
    # chara_graph: ServantFigure  # 再临卡面立绘
    commands: ServantFigure  # 指令卡
    faces: ServantFigure  # 小图（助战选框和仓库界面）
    narrow_figure: ServantFigure  # 配队界面的窄边图
    status: ServantFigure  # 进本战斗的技能图标背后的图


@dataclass
class ServantNoblePhantasm:
    id: int
    num: int
    card: str
    name: str  # EN
    original_name: str  # JP
    ruby: str  # JP
    icon: str  # url
    # other fields omitted


@dataclass
class ServantInfo:
    id: int
    atk_base: int
    atk_max: int
    attribute: str
    battle_name: str  # EN
    class_name: str
    collection_no: int
    cost: int
    extra_assets: ServantExtraAssets
    hp_base: int
    hp_max: int
    lv_max: int
    name: str  # EN
    original_battle_name: str  # JP
    original_name: str  # JP
    cards: List[str]
    noble_phantasms: List[ServantNoblePhantasm]
    # other fields are not used


@dataclass
class CraftEssenceMeta:
    atk_max: int
    collection_no: int
    face: str  # url
    flag: str
    hp_max: int
    id: int
    name: str  # EN name
    original_name: str  # JP name
    rarity: int
    type: str
    valentine_equip_owner: Optional[int] = None
    bond_equip_owner: Optional[int] = None


@dataclass
class CraftEssenceFigure:
    equip: Dict[str, str]


@dataclass
class CraftEssenceExtraAssets:
    # chara_graph: CraftEssenceFigure  # 完整的图片
    equip_face: CraftEssenceFigure  # 助战选框
    faces: CraftEssenceFigure  # 小图（仓库界面）


@dataclass
class CraftEssenceInfo:
    atk_base: int
    atk_max: int
    collection_no: int
    cost: int
    extra_assets: CraftEssenceExtraAssets
    flag: str
    hp_base: int
    hp_max: int
    id: int
    lv_max: int
    name: str  # EN
    original_name: str  # JP
    rarity: int
    type: str


tbl_name_pattern = re.compile(r'create\s+table\s+([a-zA-Z_]+)')
T = TypeVar('T')


# noinspection DuplicatedCode
def create_table_not_exists(cursor, table_sql):
    match = re.search(tbl_name_pattern, table_sql)
    if match is None:
        raise ValueError('invalid sql statement')
    table_name = match.group(1)
    cursor.execute("select count(1) from sqlite_master where type = 'table' and name = ?", (table_name,))
    if cursor.fetchone()[0] == 0:
        cursor.execute(table_sql)


def camel_to_underline(camel_format: str) -> str:
    underline_format = ''
    for char in camel_format:
        if char.isupper():
            underline_format += '_' + char.lower()
        else:
            underline_format += char
    return underline_format


def import_class_from_str(class_str: str) -> Type[T]:
    if '.' in class_str:
        module_name, class_name = class_str.rsplit('.', 1)
        return getattr(importlib.import_module(module_name), class_name)
    elif class_str in globals():
        return globals()[class_str]
    else:
        return getattr(importlib.import_module('builtins'), class_str)


def parse_json_into_dataclass(json_obj: Dict[str, Any], dataclass_type: Type[T],
                              suppress_key_not_found: bool = False) -> T:
    if not isinstance(json_obj, dict):
        return dataclass_type(json_obj)
    kwargs = {}
    for key, value in json_obj.items():
        key = camel_to_underline(key)
        if key not in dataclass_type.__annotations__:
            if not suppress_key_not_found:
                logger.warning(f'key {key} not in dataclass {dataclass_type!r}, skip parsing')
            continue
        dest_type = dataclass_type.__annotations__[key]
        dest_type_str = str(dest_type)
        if dest_type in {int, float, str, bool, dict, list}:
            kwargs[key] = dest_type(value)
            continue
        if dest_type_str.startswith('typing.'):
            dest_type_str = dest_type_str[7:]  # skip "typing."
        # handle Union type (partially support) and skip empty values
        if dest_type_str.startswith('Union['):
            if not dest_type_str.endswith(', NoneType]'):
                raise ValueError('Union type only supports NoneType')
            dest_type_str = dest_type_str[6:-11]  # skip "Union[" and ", NoneType]"
            if dest_type_str.startswith('typing.'):
                dest_type_str = dest_type_str[7:]
            if value is None:
                kwargs[key] = None  # skip None
                continue
            dest_type = dest_type.__args__[0]
        elif dest_type_str.startswith('Optional['):
            dest_type_str = dest_type_str[9:-1]  # skip "Optional[]"
            if dest_type_str.startswith('typing.'):
                dest_type_str = dest_type_str[7:]
            if value is None:
                kwargs[key] = None  # skip None
                continue
            dest_type = dest_type.__args__[0]
        # handle non-empty values
        if dest_type_str.startswith('Dict[str,'):
            dest_type_str = dest_type_str[9:-1].strip()
            dest_type = import_class_from_str(dest_type_str)
            # Dict[str, Any]
            if dest_type == Any:
                kwargs[key] = value
                continue
            if value is None:
                kwargs[key] = None
                continue
            value_dict = {}
            for inner_key, inner_value in value.items():
                value_dict[camel_to_underline(inner_key)] = parse_json_into_dataclass(inner_value, dest_type,
                                                                                      suppress_key_not_found)
            kwargs[key] = value_dict
        elif dest_type_str.startswith('List['):
            dest_type_str = dest_type_str[5:-1].strip()
            dest_type = import_class_from_str(dest_type_str)
            # List[Any]
            if dest_type == Any:
                kwargs[key] = value
                continue
            if value is None:
                kwargs[key] = None
                continue
            value_list = []
            for inner_value in value:
                value_list.append(parse_json_into_dataclass(inner_value, dest_type, suppress_key_not_found))
            kwargs[key] = value_list
        else:
            if isinstance(dest_type, str):
                dest_type = import_class_from_str(dest_type_str)
            kwargs[key] = parse_json_into_dataclass(value, dest_type, suppress_key_not_found)
    return dataclass_type(**kwargs)


def log_servant_meta(servant_meta: List[ServantMeta]) -> None:
    latest_svt_id = max(servant_meta, key=lambda x: x.collection_no)
    logger.info(f'Fetched {len(servant_meta)} servants with latest servant id {latest_svt_id.collection_no} '
                f'(name: {latest_svt_id.original_name}, internal id: {latest_svt_id.id})')


def log_ce_meta(ce_meta: List[CraftEssenceMeta]) -> None:
    latest_ce_id = max(ce_meta, key=lambda x: x.collection_no)
    logger.info(f'Fetched {len(ce_meta)} craft essences with latest ce id {latest_ce_id.collection_no} '
                f'(name: {latest_ce_id.original_name}, internal id: {latest_ce_id.id})')

# HTTP requests


def fetch_servant_meta(sess: requests.Session) -> List[ServantMeta]:
    url = 'https://api.atlasacademy.io/export/JP/basic_servant_lang_en.json'
    resp = sess.get(url)
    resp.raise_for_status()
    servant_info = resp.json()
    servant_meta = [parse_json_into_dataclass(x, ServantMeta) for x in servant_info]
    log_servant_meta(servant_meta)
    return servant_meta


def fetch_servant_info(sess: requests.Session, servant_id: int) -> ServantInfo:
    url = f'https://api.atlasacademy.io/nice/JP/servant/{servant_id}?lore=true&lang=en'
    resp = sess.get(url)
    resp.raise_for_status()
    servant_detail = resp.json()
    return parse_json_into_dataclass(servant_detail, ServantInfo, True)


def fetch_craft_essence_meta(sess: requests.Session) -> List[CraftEssenceMeta]:
    url = 'https://api.atlasacademy.io/export/JP/basic_equip_lang_en.json'
    resp = sess.get(url)
    resp.raise_for_status()
    ce_info = resp.json()
    ce_meta = [parse_json_into_dataclass(x, CraftEssenceMeta) for x in ce_info]
    log_ce_meta(ce_meta)
    return ce_meta


def fetch_craft_essence_info(sess: requests.Session, ce_id: int) -> CraftEssenceInfo:
    url = f'https://api.atlasacademy.io/nice/JP/equip/{ce_id}?lore=true&lang=en'
    resp = sess.get(url)
    resp.raise_for_status()
    ce_detail = resp.json()
    return parse_json_into_dataclass(ce_detail, CraftEssenceInfo, True)


# SQLite components


# noinspection SqlResolve
def create_sqlite_connection(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        logger.info(f'Creating new database at {db_path}')
        open(db_path, 'wb').close()
    conn = sqlite3.connect(db_path)
    csr = conn.cursor()
    create_table_not_exists(csr, "create table db_vars(key text primary key, value text)")

    create_table_not_exists(csr, "create table image(image_key text primary key, image_data blob, hash integer)")
    csr.execute("create index if not exists image_hash_index on image(hash)")
    create_table_not_exists(csr, "create table servant_meta(servant_id int primary key, meta_json text)")
    create_table_not_exists(csr, "create table craft_essence_meta(ce_id int primary key, meta_json text)")
    create_table_not_exists(csr, "create table servant_info(servant_id int primary key, info_json text)")
    create_table_not_exists(csr, "create table craft_essence_info(ce_id int primary key, info_json text)")
    for asset_name in ServantExtraAssets.__annotations__.keys():
        create_table_not_exists(csr, f"create table servant_{asset_name}(servant_id int not null, image_key text)")
        csr.execute(f"create index if not exists servant_{asset_name}_index on servant_{asset_name}(servant_id)")
    for asset_name in CraftEssenceExtraAssets.__annotations__.keys():
        create_table_not_exists(csr, f"create table craft_essence_{asset_name}(ce_id int not null, image_key text)")
        csr.execute(f"create index if not exists craft_essence_{asset_name}_index on craft_essence_{asset_name}(ce_id)")
    csr.close()
    conn.commit()
    return conn


def get_db_vars(db_conn: sqlite3.Connection, key: str) -> Optional[str]:
    csr = db_conn.cursor()
    csr.execute("select value from db_vars where key = ?", (key,))
    row = csr.fetchone()
    csr.close()
    if row is None:
        return None
    return row[0]


def set_db_vars(db_conn: sqlite3.Connection, key: str, value: str):
    csr = db_conn.cursor()
    if get_db_vars(db_conn, key) is None:
        csr.execute("insert into db_vars(key, value) values (?, ?)", (key, value))
    else:
        csr.execute("update db_vars set value = ? where key = ?", (value, key))
    csr.close()
    db_conn.commit()


def fetch_servant_meta_from_db(sess: requests.Session, db_conn: sqlite3.Connection,
                               force: bool = False) -> List[ServantMeta]:
    servant_meta = None  # set if fetched from source
    try:
        if force:  # force update
            servant_meta = fetch_servant_meta(sess)
            return servant_meta
        last_update = get_db_vars(db_conn, 'servant_info_last_update')
        cache_time = int(get_db_vars(db_conn, 'cache_time') or '0')
        if last_update is None or time() - int(last_update) > cache_time:  # cache miss
            servant_meta = fetch_servant_meta(sess)
            return servant_meta
        csr = db_conn.cursor()
        csr.execute("select servant_id, meta_json from servant_meta")
        servant_meta_from_db = []
        for row in csr.fetchall():
            servant_meta_from_db.append(parse_json_into_dataclass(json.loads(row[1]), ServantMeta))
        csr.close()
        log_servant_meta(servant_meta_from_db)
        return servant_meta_from_db
    finally:
        if servant_meta is not None:
            set_db_vars(db_conn, 'servant_info_last_update', str(int(time())))
            csr = db_conn.cursor()
            csr.executemany("insert or replace into servant_meta(servant_id, meta_json) values (?, ?)",
                            [(x.collection_no, json.dumps(asdict(x))) for x in servant_meta])
            csr.close()
            db_conn.commit()


def fetch_craft_essence_meta_from_db(sess: requests.Session, db_conn: sqlite3.Connection,
                                     force: bool = False) -> List[CraftEssenceMeta]:
    ce_meta = None  # set if fetched from source
    try:
        if force:  # force update
            ce_meta = fetch_craft_essence_meta(sess)
            return ce_meta
        last_update = get_db_vars(db_conn, 'craft_essence_info_last_update')
        cache_time = int(get_db_vars(db_conn, 'cache_time') or '0')
        if last_update is None or time() - int(last_update) > cache_time:  # cache miss
            ce_meta = fetch_craft_essence_meta(sess)
            return ce_meta
        csr = db_conn.cursor()
        csr.execute("select ce_id, meta_json from craft_essence_meta")
        ce_meta_from_db = []
        for row in csr.fetchall():
            ce_meta_from_db.append(parse_json_into_dataclass(json.loads(row[1]), CraftEssenceMeta))
        csr.close()
        log_ce_meta(ce_meta_from_db)
        return ce_meta_from_db
    finally:
        if ce_meta is not None:
            set_db_vars(db_conn, 'craft_essence_info_last_update', str(int(time())))
            csr = db_conn.cursor()
            csr.executemany("insert or replace into craft_essence_meta(ce_id, meta_json) values (?, ?)",
                            [(x.collection_no, json.dumps(asdict(x))) for x in ce_meta])
            csr.close()
            db_conn.commit()


def fetch_servant_info_from_db(sess: requests.Session, db_conn: sqlite3.Connection,
                               servant_id: int) -> ServantInfo:
    csr = db_conn.cursor()
    csr.execute("select info_json from servant_info where servant_id = ?", (servant_id,))
    row = csr.fetchone()
    if row is None:  # cache miss
        servant_info = fetch_servant_info(sess, servant_id)
        csr.execute("insert into servant_info(servant_id, info_json) values (?, ?)",
                    (servant_id, json.dumps(asdict(servant_info))))
        csr.close()
        db_conn.commit()
        return servant_info
    else:
        csr.close()
        return parse_json_into_dataclass(json.loads(row[0]), ServantInfo, True)


def fetch_craft_essence_info_from_db(sess: requests.Session, db_conn: sqlite3.Connection,
                                     ce_id: int) -> CraftEssenceInfo:
    csr = db_conn.cursor()
    csr.execute("select info_json from craft_essence_info where ce_id = ?", (ce_id,))
    row = csr.fetchone()
    if row is None:  # cache miss
        ce_info = fetch_craft_essence_info(sess, ce_id)
        csr.execute("insert into craft_essence_info(ce_id, info_json) values (?, ?)",
                    (ce_id, json.dumps(asdict(ce_info))))
        csr.close()
        db_conn.commit()
        return ce_info
    else:
        csr.close()
        return parse_json_into_dataclass(json.loads(row[0]), CraftEssenceInfo, True)


def fetch_image(sess: requests.Session, url: str) -> bytes:
    resp = sess.get(url)
    resp.raise_for_status()
    content = resp.content
    if 'content-length' in resp.headers:
        if int(resp.headers['content-length']) != len(content):
            raise Exception(f'Image size mismatch: {url}, expected {resp.headers["content-length"]}, '
                            f'got {len(content)}')
    return content


def compute_phash(img_blob: bytes) -> int:
    img = Image.open(BytesIO(img_blob))
    # noinspection PyTypeChecker
    img = np.array(img, dtype=np.uint8)
    return perception_hash(img)


# noinspection DuplicatedCode
def fetch_servant_images(sess: requests.Session, db_conn: sqlite3.Connection, servant_info: ServantInfo) -> None:
    csr = db_conn.cursor()
    for asset_name in servant_info.extra_assets.__annotations__.keys():
        servant_figure = getattr(servant_info.extra_assets, asset_name)  # type: ServantFigure
        if servant_figure is None:
            continue
        asset_dict = servant_figure.ascension
        if asset_dict is None:
            continue
        for asset_id, asset_url in asset_dict.items():
            csr.execute("select count(1) from image where image_key = ?", (asset_url,))
            is_exist = csr.fetchone()[0] > 0
            if is_exist:
                continue
            image_data = fetch_image(sess, asset_url)
            image_hash = compute_phash(image_data)
            csr.execute("insert into image(image_key, image_data, hash) values (?, ?, ?)",
                        (asset_url, image_data, image_hash))
            # noinspection SqlResolve
            csr.execute(f"insert into servant_{asset_name}(servant_id, image_key) values (?, ?)",
                        (servant_info.collection_no, asset_url))
    csr.close()
    db_conn.commit()


# noinspection DuplicatedCode
def fetch_craft_essence_images(sess: requests.Session, db_conn: sqlite3.Connection, ce_info: CraftEssenceInfo) -> None:
    csr = db_conn.cursor()
    for asset_name in ce_info.extra_assets.__annotations__.keys():
        servant_figure = getattr(ce_info.extra_assets, asset_name)  # type: CraftEssenceFigure
        if servant_figure is None:
            continue
        asset_dict = servant_figure.equip
        if asset_dict is None:
            continue
        for asset_id, asset_url in asset_dict.items():
            csr.execute("select count(1) from image where image_key = ?", (asset_url,))
            is_exist = csr.fetchone()[0] > 0
            if is_exist:
                continue
            image_data = fetch_image(sess, asset_url)
            image_hash = compute_phash(image_data)
            csr.execute("insert into image(image_key, image_data, hash) values (?, ?, ?)",
                        (asset_url, image_data, image_hash))
            # noinspection SqlResolve
            csr.execute(f"insert into craft_essence_{asset_name}(ce_id, image_key) values (?, ?)",
                        (ce_info.collection_no, asset_url))
    csr.close()
    db_conn.commit()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='cv_data/fgo_v2.db', help='sqlite db file path')
    parser.add_argument('--force', action='store_true', help='force update')
    parser.add_argument('--cache_time', default=86400*7, type=int, help='cache time in seconds (default: 7 days)')
    parser.add_argument('--proxy', default=None, type=str, help='proxy url')
    return parser.parse_known_args()[0]


def main():
    configure_logging()
    args = parse_args()
    db_conn = create_sqlite_connection(args.db)
    set_db_vars(db_conn, 'cache_time', str(args.cache_time))
    sess = requests.Session()
    if args.proxy is not None:
        proxies = {'http': args.proxy, 'https': args.proxy}
        sess.proxies = proxies
    for servant in fetch_servant_meta_from_db(sess, db_conn, args.force):
        logger.info(f'Fetching servant {servant.collection_no} ({servant.original_name})')
        servant_info = fetch_servant_info_from_db(sess, db_conn, servant.collection_no)
        fetch_servant_images(sess, db_conn, servant_info)
    for craft_essence in fetch_craft_essence_meta_from_db(sess, db_conn, args.force):
        logger.info(f'Fetching craft essence {craft_essence.collection_no} ({craft_essence.original_name})')
        craft_essence_info = fetch_craft_essence_info_from_db(sess, db_conn, craft_essence.collection_no)
        fetch_craft_essence_images(sess, db_conn, craft_essence_info)


if __name__ == '__main__':
    main()
