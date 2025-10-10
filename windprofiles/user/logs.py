import logging
import logging.handlers
import json
import time
from multiprocessing import Queue
import sys
import traceback


class CutelogJSONFormatter(logging.Formatter):
    """JSON formatter for Cutelog-compatible logs."""

    def format(self, record):
        log_obj = {
            "created": getattr(record, "created", time.time()),
            "asctime": self.formatTime(record, self.datefmt),
            "name": record.name,
            "levelname": record.levelname,
            "levelno": record.levelno,
            "pathname": record.pathname,
            "lineno": record.lineno,
            "msg": record.getMessage(),
            "process": record.process,
            "thread": record.thread,
        }

        if record.exc_info:
            log_obj["exc_text"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        return json.dumps(log_obj, ensure_ascii=False)


def get_main_logger(logfile, clear: bool = False):
    if clear:
        with open(logfile, "w") as _:
            pass
    root = logging.getLogger("MAIN")
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    fh = logging.FileHandler(logfile, mode="a", encoding="utf-8")
    fh.setFormatter(CutelogJSONFormatter())
    root.addHandler(fh)
    return root


def listener_configurer(logfile):
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    fh = logging.FileHandler(logfile, mode="a", encoding="utf-8")
    fh.setFormatter(CutelogJSONFormatter())
    root.addHandler(fh)
    root.setLevel(logging.DEBUG)


def log_listener(queue: Queue, logfile: str):
    listener_configurer(logfile)
    while True:
        try:
            record = queue.get()
            if record is None:  # Sentinel to stop listener
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            print("Logging listener error:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def configure_worker(queue: Queue):
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    qh = logging.handlers.QueueHandler(queue)
    root.addHandler(qh)
    root.setLevel(logging.DEBUG)
