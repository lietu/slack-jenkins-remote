import logging
from time import time


# http://code.activestate.com/recipes/325905-memoize-decorator-with-timeout/
class MWT(object):
    """Memoize With Timeout"""
    _caches = {}
    _timeouts = {}

    def __init__(self, timeout=2):
        self.timeout = timeout

    def collect(self):
        """Clear cache of results which have timed out"""
        for func in self._caches:
            cache = {}
            for key in self._caches[func]:
                if (time() - self._caches[func][key][1]) < \
                        self._timeouts[func]:
                    cache[key] = self._caches[func][key]
            self._caches[func] = cache

    def __call__(self, f):
        self.cache = self._caches[f] = {}
        self._timeouts[f] = self.timeout

        def func(*args, **kwargs):
            kw = kwargs.items()
            kw.sort()
            key = (args, tuple(kw))
            try:
                v = self.cache[key]
                if (time() - v[1]) > self.timeout:
                    raise KeyError
            except KeyError:
                v = self.cache[key] = f(*args, **kwargs), time()
            return v[0]

        func.func_name = f.func_name

        return func


def format_timedelta(delta):
    seconds = delta.seconds

    if seconds <= 0:
        return "no time"

    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    parts = []
    if hours:
        if hours == 1:
            parts.append("{} hour".format(hours))
        else:
            parts.append("{} hours".format(hours))
    if minutes:
        if minutes == 1:
            parts.append("{} minute".format(minutes))
        else:
            parts.append("{} minutes".format(minutes))
    if seconds:
        if seconds == 1:
            parts.append("{} second".format(seconds))
        else:
            parts.append("{} seconds".format(seconds))

    return " ".join(parts)


def format_params(params):
    desc = []
    for key in params:
        desc.append("`{}={}`".format(key, params[key]))

    if desc:
        return ", ".join(desc)
    else:
        return "using defaults"


def setup_logger(app):
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    ch.setFormatter(
        logging.Formatter('%(asctime)s [%(levelname)8s] %(message)s')
    )

    app.logger.addHandler(ch)
    app.logger.setLevel(logging.DEBUG)
