# test deadlock

import logging
import logging.config

class CustomHandler(logging.Handler):
    def emit(self, record):
        pass
        # logger.setLevel(logging.INFO)
        # logger.isEnabledFor(logging.INFO)

def config_once():
    print("hello from config_once")

    logging.config.dictConfig({
            'version': 1, 
            'handlers': {
                # 'custom': {'class': 'logging_deadlock.CustomHandler'}
            },
            'root': {
                # 'handlers': ['custom']
            }
        }
    )


if __name__ == '__main__':
config_once()

