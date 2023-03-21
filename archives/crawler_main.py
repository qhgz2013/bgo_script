import requests
import sqlite3
import argparse
import re
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO, BytesIO
from warnings import warn
import os
import sys
from time import sleep


def initialize_sql_table(sql_conn):
    tbl_name_pattern = re.compile(r'create\s+table\s+([a-zA-Z_]+)')
    cursor = sql_conn.cursor()

    def create_table_not_exists(table_sql):
        match = re.search(tbl_name_pattern, table_sql)
        if match is None:
            raise ValueError('invalid sql statement')
        table_name = match.group(1)
        cursor.execute("select count(1) from sqlite_master where type = 'table' and name = ?", (table_name,))
        if cursor.fetchone()[0] == 0:
            cursor.execute(table_sql)

    create_table_not_exists('create table image(image_key varchar(50) primary key not null unique,'
                            'name varchar(50), image_data blob not null)')
    create_table_not_exists('create table servant_icon(id int not null, image_key varchar(50) not null,'
                            'foreign key (image_key) references image(image_key))')
    create_table_not_exists('create table servant_command_card_icon(id int not null, image_key varchar(50) not null,'
                            'foreign key (image_key) references image(image_key))')
    create_table_not_exists('create table craft_essence_icon(id int not null, image_key varchar(50) not null,'
                            'foreign key (image_key) references image(image_key))')
    create_table_not_exists('create table image_sift_descriptor(image_key varchar(50) primary key not null unique,'
                            'key_points blob not null, descriptors blob not null,'
                            'foreign key (image_key) references image(image_key))')
    create_table_not_exists('create table servant_np(id int not null unique primary key, np_type int not null)')
    cursor.close()
    sql_conn.commit()


def download_image_if_not_exists(sess, sql_cursor, image_key, image_text, url, retry_count=5, retry_delay=3,
                                 *args, **kwargs):
    assert image_key is not None and len(image_key) > 0, "image_key should not be empty"
    sql_cursor.execute("select count(*) from image where image_key = ?", (image_key,))
    if sql_cursor.fetchone()[0] == 0:
        if image_text is None or image_key == image_text:
            print('image key', image_key, 'miss, downloading from', url)
        else:
            print('image key', image_key, '( name:', image_text, ') miss, downloading from', url)
        for _ in range(retry_count):  # retry: 5
            try:
                request = sess.get(url, *args, **kwargs)
                sql_cursor.execute("insert into image (image_key, name, image_data) values (?, ?, ?)",
                                   (image_key, image_text, request.content))
                break
            except Exception as e:
                warn(f'Failed to download {url}: {e}')
                sleep(retry_delay)


def retrieve_servant_icons(sql_conn):
    prefix = 'https://fategrandorder.fandom.com'
    scale_down_ptn = re.compile(r'/scale-to-(width|height)-down/\d+')
    cursor = sql_conn.cursor()
    # noinspection SqlWithoutWhere
    cursor.execute("delete from servant_icon")
    # noinspection SqlWithoutWhere
    cursor.execute("delete from servant_np")
    sess = requests.session()
    icon_url = f'{prefix}/wiki/Servant_List_by_ID'
    html = BeautifulSoup(sess.get(icon_url).text, features='html.parser')
    tables = html.find_all('table', {'class': 'wikitable'})
    ids = set()
    np_type = {'arts': 3, 'quick': 2, 'buster': 1, 'missing': None}
    for i, table in enumerate(tables):
        rows = table.find_all('tr')[1:]
        for j, row in enumerate(rows):
            cols = row.find_all('td')
            servant_url = prefix + cols[1].a.attrs['href']
            print(f'retrieving {i+1}/{len(tables)} -> {j+1}/{len(rows)}: {servant_url} ')
            servant_id = int(str(cols[-1].string).replace('\n', '').replace(' ', ''))
            if servant_id in ids:
                continue
            ids.add(servant_id)
            servant_html = BeautifulSoup(sess.get(servant_url).text, features='html.parser')
            # Retrieving servant icons (used for support servant auto selection)
            icon_div = servant_html.find('div', {'id': 'gallery-2'})
            try:
                np_html = servant_html.find('span', {'id': 'Noble_Phantasm'})
                np_html = np_html.find_next('div', {'class': 'tabber'})
                np = []
                np_default = []

                def _match_tabber_recursive(root_node, default=False):
                    tab_content = root_node.find_all('div', {'class': 'wds-tab__content'}, recursive=False)
                    tab_label = root_node.find('div', {'class': 'wds-tabs__wrapper'}, recursive=False).find_all('li')
                    # tab_label = root_node.find_all('li', {'class': 'wds-tabs__tab'}, recursive=False)
                    tab_label = [''.join(x.strings) for x in tab_label]
                    for label, content in zip(tab_label, tab_content):
                        tabber_inner = content.find('div', {'class': 'tabber'})
                        if tabber_inner is not None:
                            _match_tabber_recursive(tabber_inner, default)
                            # return
                        np_table = content.find_all('table', {'class': 'wikitable'}, recursive=False)
                        is_default = 'default' in label.lower()
                        if len(np_table) == 0:
                            continue
                        try:
                            np_img = np_table[-1].tbody.tr.th.a.img
                            np_img = np_img.attrs['alt'].split('.')[0].lower()
                            if is_default:
                                np_default.append(np_type[np_img])
                            else:
                                np.append(np_type[np_img])
                        except AttributeError:
                            continue
                        except KeyError as e:
                            warn(f'Exception for parsing servant {servant_id} np: {e}')
                            continue

                _match_tabber_recursive(np_html)
                if len(np) == 0 and len(np_default) == 0:
                    warn(f'Could not find NP for servant {servant_id}')
                    np = None
                else:
                    if len(np_default) != 0:
                        first_type = np_default[0]
                        for ii in range(1, len(np_default)):
                            if np_default[ii] != first_type:
                                warn(f'Mismatch NP type for servant {servant_id}')
                        np = first_type
                    else:
                        first_type = np[0]
                        for ii in range(1, len(np)):
                            if np[ii] != first_type:
                                warn(f'Mismatch NP type for servant {servant_id}')
                        np = first_type
            except AttributeError:
                warn(f'Could not find NP for servant {servant_id}')
                np = None
            if np is not None:
                cursor.execute("insert into servant_np(id, np_type) values (?, ?)", (servant_id, np))
            icon_items = icon_div.find_all('div', {'class': 'wikia-gallery-item'})
            for item in icon_items:
                caption_obj = item.find('div', {'class': 'lightbox-caption'})
                text = caption_obj.string or ''.join(caption_obj.strings)
                img = item.find('img')
                img_src = img.attrs['src']
                img_key = img.attrs['data-image-name']
                text_lower = text.lower()
                img_src = re.sub(scale_down_ptn, '', img_src)
                # skips portrait, without-frame images and April Fool icons
                ignore = False
                for candidate in ['portrait', 'without frame', 'april', 'fool', 'np logo']:
                    if candidate in text_lower:
                        ignore = True
                        break
                # skips "status" icons (same as portrait, but in another strange naming rule)
                if not ignore and 'status' in img_key:
                    ignore = True
                if ignore:
                    continue
                download_image_if_not_exists(sess, cursor, img_key, text, img_src)
                cursor.execute("insert into servant_icon(id, image_key) values (?, ?)", (servant_id, img_key))
            # Retrieving servant in-battle command card sprites (used for command card recognition)
            # icon_div = servant_html.find('div', {'class': 'tabbertab', 'title': 'Sprites'})
            # icon_div = icon_div or servant_html.find('div', {'class': 'tabbertab', 'title': 'Sprite'})
            icon_div = servant_html.find('div', {'id': 'gallery-3'})
            if icon_div is None:
                warn('Could not retrieve sprites from HTML of servant #%d' % servant_id, RuntimeWarning)
                continue
            icon_items = icon_div.find_all('div', {'class': 'wikia-gallery-item'})
            has_command_card = False
            for item in icon_items:
                text = str(item.find('div', {'class': 'lightbox-caption'}).string)
                img = item.find('img')
                if img is None:
                    continue
                img_src = img.attrs['src']
                img_key = img.attrs['data-image-name']
                text_lower = text.lower()
                img_src = re.sub(scale_down_ptn, '', img_src)
                # skips portrait and without-frame images
                if 'command card' in text_lower:
                    has_command_card = True
                    download_image_if_not_exists(sess, cursor, img_key, text, img_src)
                    cursor.execute("insert into servant_command_card_icon(id, image_key) values (?, ?)",
                                   (servant_id, img_key))
            if not has_command_card:
                warn('No command card found for servant #%d' % servant_id, RuntimeWarning)
    cursor.close()
    sql_conn.commit()


def retrieve_craft_essence_icons(sql_conn):
    cursor = sql_conn.cursor()
    # noinspection SqlWithoutWhere
    cursor.execute("delete from craft_essence_icon")
    sess = requests.session()
    url = 'https://fgo.wiki/w/%E7%A4%BC%E8%A3%85%E5%9B%BE%E9%89%B4'
    csv_pattern = re.compile('function\\s+get_csv\\(\\)\\s*\n\\s*{\\s*\n\\s*var\\s+raw_str\\s*=\\s*"([^"]+)"')
    # craft_essence_url_pattern = re.compile('(/images/[0-9a-f]/[0-9a-f]{2}/[^ ]+)')
    html = sess.get(url).text
    csv_str = re.search(csv_pattern, html).group(1).replace('\\n', '\n')
    with StringIO(csv_str) as f:
        data_frame = pd.read_csv(f)
    ids = data_frame.id
    ids_rev_mapper = {j: i for i, j in enumerate(ids)}
    # changed from icon to full image
    # don't know why it is changed to such an idiot mode
    try:
        name_link = data_frame.name_link
    except AttributeError:
        override_pattern = re.compile('override_data\\s*=\\s*"([^"]+)"')
        override_match = re.search(override_pattern, html)
        if override_match is None:
            raise RuntimeError('could not find name_link')
        override_data = override_match.group(1).replace('\\n', '\n').split('\n')
        name_link = [None] * data_frame.shape[0]
        cur_id = 0
        for line in override_data:
            if line.startswith('id='):
                cur_id = int(line[3:])
            elif line.startswith('name_link='):
                name_link[ids_rev_mapper[cur_id]] = line[10:]
    name = name_link
    retry_cnt = 5
    for i in range(data_frame.shape[0]):
        img_key = name_link[i]
        html_url = f'https://fgo.wiki/w/{img_key}'
        for j in range(retry_cnt):
            try:
                print(f'retrieving {i+1}/{data_frame.shape[0]} {html_url}')
                resp = sess.get(html_url)
                assert resp.ok, f'HTTP request failed with status code {resp.status_code}'
                html = BeautifulSoup(resp.text, features='html.parser').find('td', attrs={'id': f'CEGraph-{ids[i]}'})
                img_attrs = html.find('img').attrs
                # original image is not used here, too big!
                # candidate_src = img_attrs['data-srcset']
                # img_url = 'https://fgo.wiki' + re.search(craft_essence_url_pattern, candidate_src).group(1)
                img_url = 'https://fgo.wiki' + img_attrs['data-src']
                download_image_if_not_exists(sess, cursor, img_key, name[i], img_url)
                cursor.execute("insert into craft_essence_icon(id, image_key) values (?, ?)", (int(ids[i]), img_key))
                break
            except Exception as ex:
                warn(f'Failed to download {name[i]} (id: {ids[i]}): {ex}, retrying {j+1}/{retry_cnt}')
    cursor.close()
    sql_conn.commit()


def pre_compute_sift_features(sql_conn):
    try:
        from image_process import sift_class
        from util import pickle_dumps
        from PIL import Image
        import numpy as np
    except ImportError:
        print('Required dependency (cv2, pillow, numpy) is not satisfied, skipping sift pre-computation')
        return
    if sift_class is None:
        print('No SIFT detector found in current OpenCV, ignored')
        return
    # noinspection PyUnresolvedReferences
    try:
        sift = sift_class.create()
    except cv2.error:
        print('SIFT is disable for current build, rebuild OpenCV with OPENCV_ENABLE_NONFREE with contrib modules')
        return
    print('Pre-computing SIFT features')
    cursor = sql_conn.cursor()
    cursor.execute("select image_key from image where image_key not in (select image_key from image_sift_descriptor)")
    image_keys = cursor.fetchall()
    for image_key, in image_keys:
        cursor.execute("select image_data from image where image_key = ?", (image_key,))
        blob = cursor.fetchone()[0]
        with BytesIO(blob) as f:
            img = np.asarray(Image.open(f), 'uint8')
        key_points, descriptors = sift.detectAndCompute(img, None)
        key_points = [(x.pt, x.size, x.angle, x.response, x.octave, x.class_id) for x in key_points]
        key_points_blob = pickle_dumps(key_points)
        descriptors_blob = pickle_dumps(descriptors)
        cursor.execute("insert into image_sift_descriptor(image_key, key_points, descriptors) values (?, ?, ?)",
                       (image_key, key_points_blob, descriptors_blob))
    cursor.close()
    sql_conn.commit()


def main():
    sys.path.append(os.path.abspath(os.curdir))
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', dest='output_db_path', help='the output path of the generated database', required=True)
    args = parser.parse_args()
    conn = sqlite3.connect(args.output_db_path)
    initialize_sql_table(conn)
    retrieve_servant_icons(conn)
    retrieve_craft_essence_icons(conn)
    pre_compute_sift_features(conn)
    conn.close()


if __name__ == '__main__':
    main()
