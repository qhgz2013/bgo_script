import sqlite3
import os


if __name__ == '__main__':
    conn = sqlite3.connect('../cv_data/fgo_v2.db')
    cursor = conn.cursor()
    cursor.execute("select image_key, image_data from image")
    os.makedirs('exported_images', exist_ok=True)
    for image_key, image_data in cursor.fetchall():
        with open('exported_images/%s' % image_key.split('/', 3)[-1].replace('/', '_').split('?')[0], 'wb') as f:
            f.write(image_data)
    cursor.close()
    conn.close()
