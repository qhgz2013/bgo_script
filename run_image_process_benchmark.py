from _logging_config import script_logger_root
import image_process

if __name__ == '__main__':
    script_logger_root.info('Starting benchmark')
    image_process.run_all_benchmark()
