import logging
import sys

from tdp.scene_manager import start_app


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


if __name__ == "__main__":
    # dev shortcut for jumping straight to game
    if len(sys.argv) > 2:
        start_app(sys.argv[1], sys.argv[2])
    else:
        start_app()
