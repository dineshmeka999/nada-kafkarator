import logging

bind = "0.0.0.0:8080"
accesslog = logging.getLogger("hypercorn.access")
errorlog = logging.getLogger("hypercorn.error")
