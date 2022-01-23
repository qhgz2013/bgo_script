import threading
from contextlib import contextmanager


class RWLock:
    def __init__(self):
        self.w_lock = threading.RLock()  # locking writes
        self.r_lock = threading.RLock()  # locking r_lock_num modification
        self.r_lock_num = 0

    def r_acquire(self):
        self.r_lock.acquire()
        self.r_lock_num += 1
        if self.r_lock_num == 1:
            self.w_lock.acquire()
        self.r_lock.release()

    def r_release(self):
        assert self.r_lock_num > 0
        self.r_lock.acquire()
        self.r_lock_num -= 1
        if self.r_lock_num == 0:
            self.w_lock.release()
        self.r_lock.release()

    def w_acquire(self):
        return self.w_lock.acquire()

    def w_release(self):
        return self.w_lock.release()

    @contextmanager
    def r_locked(self):
        try:
            self.r_acquire()
            yield
        finally:
            self.r_release()

    @contextmanager
    def w_locked(self):
        try:
            self.w_acquire()
            yield
        finally:
            self.w_release()
