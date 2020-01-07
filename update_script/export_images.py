import sqlite3
import os


if __name__ == '__main__':
    conn = sqlite3.connect('../cv_data/fgo_new.db')
    cursor = conn.cursor()
    cursor.execute("select image_key, image_data from image")
    os.makedirs('exported_images')
    for image_key, image_data in cursor.fetchall():
        with open('exported_images/%s' % image_key, 'wb') as f:
            f.write(image_data)
    cursor.close()
    conn.close()
