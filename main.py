# noinspection PyUnresolvedReferences
import _logging_config  # PLACE IT TO THE FIRST LINE OF IMPORT TO ENABLE GLOBAL LOGGING HOOK
from attacher import MumuAttacher, DummyAttacher
from fsm import FgoFSMFacade

dbg = False


def main():
    attacher = DummyAttacher if dbg else MumuAttacher
    script = FgoFSMFacade(attacher())
    script.run()


if __name__ == '__main__':
    main()
