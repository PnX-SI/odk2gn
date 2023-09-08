import logging

MODULE_CODE = "ODK2GN"
MODULE_PICTO = "fa-map-marker"

import colorlog


handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s%(levelname)s:%(name)s:%(message)s"))

root_logger = logging.getLogger("app")
root_logger.addHandler(handler)
root_logger.propagate = False
