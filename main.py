# noinspection PyUnresolvedReferences
import _logging_config  # PLACE IT TO THE FIRST LINE OF IMPORT TO ENABLE GLOBAL LOGGING HOOK
from attacher import MumuAttacher
from fsm import FgoFSMFacade


def main():
    script = FgoFSMFacade(MumuAttacher())
    script.run()


if __name__ == '__main__':
    main()
