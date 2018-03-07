from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import functools
import json
import numpy as np
import os
import pickle
import sys


def str2bool(x):
    x = x.strip().lower()
    if x in ['t', 'true', 'y', 'yes', '1']:
        return True
    if x in ['f', 'false', 'n', 'no', '0']:
        return False
    raise ValueError('warning: unclear value: {}'.format(x))


def str2bool_or_none(x):
    try:
        return str2bool(x)
    except ValueError:
        return None


def bool2str(x):
    return str(x).lower()


def default_if_none(x, value):
    return value if x is None else x


def harmonic_mean(*args):
    assert all([x >= 0 for x in args])
    if any([x == 0 for x in args]):
        return 0.
    return np.asscalar(1. / np.mean(1. / np.asfarray(args)))


def geometric_mean(*args):
    assert all([x >= 0 for x in args])
    if any([x == 0 for x in args]):
        return 0.
    return np.asscalar(np.exp(np.mean(np.log(args))))


def cache(protocol, filename, func, makedir=True, ignore_existing=False, verbose=False):
    '''Caches the result of a function in a file.

    Args:
        func -- Function with no arguments.
        makedir -- Create parent directory if it does not exist.
        ignore_existing -- Ignore existing cache file and call function.
            If it existed, the old cache file will be over-written.
    '''
    if (not ignore_existing) and os.path.exists(filename):
        if verbose:
            print('load from cache: {}'.format(filename), file=sys.stderr)
        with open(filename, 'r') as r:
            result = protocol.load(r)
    else:
        dir = os.path.dirname(filename)
        if makedir and (not os.path.exists(dir)):
            os.makedirs(dir)
        result = func()
        # Write to a temporary file and then perform atomic rename.
        # This guards against partial cache files.
        tmp = filename + '.tmp'
        with open(tmp, 'w') as w:
            protocol.dump(result, w)
        os.rename(tmp, filename)
    return result


cache_json = functools.partial(cache, json)
cache_pickle = functools.partial(cache, pickle)


class TimeSeries(object):
    '''Dictionary with keys in sorted order.'''

    def __init__(self, frames=None):
        self._frames = {} if frames is None else dict(frames)

    def __len__(self):
        return len(self._frames)

    def __getitem__(self, t):
        return self._frames[t]

    def __setitem__(self, t, value):
        self._frames[t] = value

    def __delitem__(self, t):
        del self._frames[t]

    def get(self, t, default):
        return self._frames.get(t, default)

    def setdefault(self, t, default):
        return self._frames.setdefault(t, default)

    def keys(self):
        '''Returns times in sequential order.'''
        return sorted(self._frames.keys())

    def values(self):
        return self._frames.values()

    def items(self):
        '''Returns (time, value) pairs in sequential order.'''
        times = sorted(self._frames.keys())
        return zip(times, [self._frames[t] for t in times])

    def __iter__(self):
        for t in sorted(self._frames.keys()):
            yield t


# class Track(object):
#
#     def __init__(self, init_time, init_rect, final_time=None, annotations=None):
#         self.init_time = init_time
#         self.init_rect = init_rect
#         self.final_time = None
#         self.annotations = None
#         self.attributes = None


class VideoObjectDict(object):
    '''Represents map video -> object -> element.
    Behaves as a dictionary with keys of (video, object) tuples.

    Example:
        for key in tracks.keys():
            print(tracks[key])

        tracks = VideoObjectDict()
        ...
        for vid in tracks.videos():
            for obj in tracks.objects(vid):
                print(tracks[(vid, obj)])
    '''

    def __init__(self, elems=None):
        self._elems = {} if elems is None else dict(elems)

    def videos(self):
        return set([vid for vid, obj in self._elems.keys()])

    def objects(self, vid):
        # TODO: This is somewhat inefficient if called for all videos.
        return [obj_i for vid_i, obj_i in self._elems.keys() if vid_i == vid]

    def __len__(self):
        return len(self._elems)

    def __getitem__(self, key):
        return self._elems[key]

    def __setitem__(self, key, value):
        self._elems[key] = value

    def __delitem__(self, key):
        del self._elems[key]

    def keys(self):
        return self._elems.keys()

    def values(self):
        return self._elems.values()

    def items(self):
        return self._elems.items()

    def __iter__(self):
        for k in self._elems.keys():
            yield k

    def to_nested_dict(self):
        elems = {}
        for (vid, obj), elem in self._elems.items():
            elems.setdefault(vid, {})[obj] = elem

    def update_from_nested_dict(self, elems):
        for vid, vid_elems in elems.items():
            for obj, elem in vid_elems.items():
                self._elems[(vid, obj)] = elem
