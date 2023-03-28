import logging
import sys

from tdp.scene_manager import start_app


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


if __name__ == "__main__":
    start_app()
