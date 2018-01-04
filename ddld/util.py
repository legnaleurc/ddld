import argparse
import collections
import datetime as dt
import functools as ft
import logging
import math
import os.path as op
import signal
import sys
import threading
import time

from tornado import ioloop as ti, web as tw, httpserver as ths
from wcpan.logger import setup as setup_logger, INFO

from . import api, view
from .controller import RootController


class LogQueue(logging.Handler):

    def __init__(self, level=logging.NOTSET):
        super(LogQueue, self).__init__(level)

        self._queue = collections.deque(maxlen=10)
        self._sockets = {}
        # log may happens in other threads, while the sockets may be removed in
        # the main thread
        self._socket_lock = threading.Lock()

    def emit(self, record):
        log = {
            'level': record.levelno,
            'timestamp': math.floor(record.created * 1000),
            'thread': record.threadName,
            'message': record.message,
        }
        self._push(log)

    def get_recent(self):
        return list(self._queue)

    def add(self, id_, ws):
        with self._socket_lock:
            if id_ in self._sockets:
                return False
            self._sockets[id_] = ws
            return True

    def remove(self, id_):
        with self._socket_lock:
            if id_ not in self._sockets:
                return False
            del self._sockets[id_]
            return True

    def _push(self, log):
        self._queue.append(log)
        with self._socket_lock:
            for id_, ws in self._sockets.items():
                ws.write_message(log)


def get_local_timezone():
    offset = time.timezone if time.daylight == 0 else time.altzone
    offset = dt.timedelta(seconds=offset)
    return dt.timezone(offset)


def parse_args(args):
    parser = argparse.ArgumentParser('ddld')

    parser.add_argument('-l', '--listen', required=True, type=int)
    parser.add_argument('-r', '--root', required=True, type=str)

    args = parser.parse_args(args)

    return args


def main(args=None):
    if args is None:
        args = sys.argv

    main_loop = ti.IOLoop.instance()
    main_loop.add_callback(amain, args)
    main_loop.start()
    main_loop.close()
    return 0


async def amain(args):
    args = parse_args(args[1:])

    loggers = setup_logger((
        'tornado.access',
        'tornado.application',
        'tornado.general',
        'requests.packages.urllib3.connectionpool',
        'wcpan.drive.google',
        'wcpan.worker',
        'ddld',
    ), '/tmp/ddld.log')
    logs = LogQueue(logging.DEBUG)
    for logger in loggers:
        logger.addHandler(logs)

    main_loop = ti.IOLoop.instance()
    controller = RootController(args.root)

    await controller.initialize()

    async def close_root():
        await controller.close()
        main_loop.stop()
    def close_signal(signum, frame):
        main_loop.add_callback_from_signal(close_root)
    signal.signal(signal.SIGINT, close_signal)

    static_path = op.join(op.dirname(__file__), 'static')
    application = tw.Application([
        (r'/api/v1/nodes', api.NodesHandler),
        (r'/api/v1/nodes/([a-zA-Z0-9\-_]+)', api.NodesHandler),
        (r'/api/v1/cache', api.CacheHandler),
        (r'/api/v1/cache/([a-zA-Z0-9\-_]+)', api.CacheHandler),
        (r'/', view.IndexHandler),
        (r'/api/v1/log', api.LogHandler),
        (r'/api/v1/socket', api.LogSocketHandler),
    ], static_path=static_path, controller=controller, logs=logs)
    server = ths.HTTPServer(application)
    server.listen(args.listen)

    INFO('ddld') << 'ready'

    return 0
