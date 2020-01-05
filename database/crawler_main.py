import requests
import sqlite3
import argparse
import re
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO, BytesIO


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
    create_table_not_exists('create table craft_essence_icon(id int not null, image_key varchar(50) not null,'
                            'foreign key (image_key) references image(image_key))')
    create_table_not_exists('create table image_sift_descriptor(image_key varchar(50) primary key not null unique,'
                            'key_points blob not null, descriptors blob not null,'
                            'foreign key (image_key) references image(image_key))')
    cursor.close()
    sql_conn.commit()


def download_image_if_not_exists(sql_cursor, image_key, image_text, url, *args, **kwargs):
    assert image_key is not None and len(image_key) > 0, "image_key should not be empty"
    sql_cursor.execute("select count(*) from image where image_key = ?", (image_key,))
    if sql_cursor.fetchone()[0] == 0:
        if image_text is None or image_key == image_text:
            print('image key', image_key, 'miss, downloading from', url)
        else:
            print('image key', image_key, '( name:', image_text, ') miss, downloading from', url)
        request = requests.get(url, *args, **kwargs)
        sql_cursor.execute("insert into image (image_key, name, image_data) values (?, ?, ?)",
                           (image_key, image_text, request.content))


def retrieve_servant_icons(sql_conn):
    cursor = sql_conn.cursor()
    cursor.execute("delete from servant_icon")
    icon_url = 'https://fategrandorder.fandom.com/wiki/Servant_List_by_ID'
    html = BeautifulSoup(requests.get(icon_url).text, features='html.parser')
    table = html.find('div', {'id': 'flytabs_ServantListByID'})
    pages = [('https://fategrandorder.fandom.com%s?action=render' % x.attrs['href']) for x in table.find_all('a')]
    for page in pages:
        html = BeautifulSoup(requests.get(page).text, features='html.parser')
        table = html.find('table', {'class': 'wikitable sortable'})
        rows = table.find_all('tr')[1:]
        ids = set()
        for row in rows:
            cols = row.find_all('td')
            servant_url = cols[1].a.attrs['href']
            print('retrieving', servant_url)
            servant_id = int(str(cols[-1].string).replace('\n', '').replace(' ', ''))
            if servant_id in ids:
                continue
            ids.add(servant_id)
            servant_html = BeautifulSoup(requests.get(servant_url).text, features='html.parser')
            icon_div = servant_html.find('div', {'id': 'gallery-2'})
            icon_items = icon_div.find_all('div', {'class': 'wikia-gallery-item'})
            for item in icon_items:
                text = str(item.find('div', {'class': 'lightbox-caption'}).string)
                img = item.find('img')
                img_src = img.attrs['src']
                img_key = img.attrs['data-image-name']
                download_image_if_not_exists(cursor, img_key, text, img_src)
                cursor.execute("insert into servant_icon(id, image_key) values (?, ?)", (servant_id, img_key))
    cursor.close()
    sql_conn.commit()


def retrieve_craft_essence_icons(sql_conn):
    cursor = sql_conn.cursor()
    cursor.execute("delete from craft_essence_icon")
    url = 'https://fgo.wiki/w/%E7%A4%BC%E8%A3%85%E5%9B%BE%E9%89%B4'
    csv_pattern = re.compile('function\\s+get_csv\\(\\)\\s*\n\\s*{\\s*\n\\s*var\\s+raw_str\\s*=\\s*"([^"]+)"')
    csv_str = re.search(csv_pattern, requests.get(url).text).group(1).replace('\\n', '\n')
    with StringIO(csv_str) as f:
        data_frame = pd.read_csv(f)
    ids = data_frame.id
    icons = data_frame.icon
    for i in range(data_frame.shape[0]):
        img_key = icons[i].split('/')[-1]
        download_image_if_not_exists(cursor, img_key, None, 'https://fgo.wiki%s' % icons[i])
        cursor.execute("insert into craft_essence_icon(id, image_key) values (?, ?)", (int(ids[i]), img_key))
    cursor.close()
    sql_conn.commit()


def pre_compute_sift_features(sql_conn):
    try:
        import cv2
        from PIL import Image
        import numpy as np
        import pickle
    except ImportError:
        print('Required dependency (cv2, pillow, numpy) is not satisfied, skipping sift pre-computation')
        return
    # noinspection PyUnresolvedReferences
    try:
        # noinspection PyUnresolvedReferences
        sift = cv2.xfeatures2d_SIFT.create()
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
        key_points_blob = pickle.dumps(key_points)
        descriptors_blob = pickle.dumps(descriptors)
        cursor.execute("insert into image_sift_descriptor(image_key, key_points, descriptors) values (?, ?, ?)",
                       (image_key, key_points_blob, descriptors_blob))
    cursor.close()
    sql_conn.commit()


def main():
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
