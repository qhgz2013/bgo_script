__all__ = ['pickle_load', 'pickle_dump', 'pickle_loads', 'pickle_dumps']

import pickle
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO


def pickle_dump(obj, fp, allow_compression=True):
    if allow_compression:
        fp.write(b'\x01')
        with ZipFile(fp, 'w', compression=ZIP_DEFLATED) as zip_fp:
            with zip_fp.open('__compressed', 'w') as zip_fp_internal:
                pickle.dump(obj, zip_fp_internal)
    else:
        fp.write(b'\x00')
        pickle.dump(obj, fp)


def pickle_load(fp):
    indicator = fp.read(1)
    if len(indicator) == 0:
        raise EOFError('Early EOF')
    indicator = ord(indicator)
    if indicator == 0:
        return pickle.load(fp)
    elif indicator == 1:
        with ZipFile(fp, 'r') as zip_fp:
            with zip_fp.open('__compressed') as zip_fp_internal:
                return pickle.load(zip_fp_internal)
    else:
        raise ValueError('Invalid compression indicator')


def pickle_dumps(obj, allow_compression=True):
    with BytesIO() as f:
        pickle_dump(obj, f, allow_compression)
        f.seek(0)
        return f.read()


def pickle_loads(blob):
    with BytesIO(blob) as f:
        return pickle_load(f)
