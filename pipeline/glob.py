from __future__ import unicode_literals

import os
import re
import fnmatch

from pipeline.storage import default_storage

__all__ = ["glob", "iglob"]


def glob(pathname):
    """Return a list of paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la fnmatch.

    """
    return sorted(list(iglob(pathname)))


def iglob(pathname):
    """Return an iterator which yields the paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la fnmatch.

    The pattern may also contain '**' to denote a recursion root.

    """
    if '**' in pathname:
        # More than one appearance of '**' is redundant as we would
        # walk there anyway
        recurse_root, pattern = pathname.split('**', 1)
        recurse_dirs = _glob_simple(recurse_root)
        for path in recurse_dirs:
            # Cases:
            # pattern is expected /*.{js,css,less,coffee} etc
            # eg js/**/*.js
            # will find js/f.js, js/foo/bar.js js/foo/bar/bat/baz/fux.js etc
            pattern = pattern.lstrip('/')
            for obj in _rglob(pattern, path):
                yield obj
    else:
        for obj in _glob_simple(pathname):
            yield obj

def _glob_simple(pathname):
    """Return an iterator which yields the paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la fnmatch.
    """
    if not has_magic(pathname):
        try:
            if default_storage.exists(pathname):
                yield pathname
        except NotImplementedError:
            # Being optimistic
            yield pathname
        return
    dirname, basename = os.path.split(pathname)
    if not dirname:
        for name in _listdir_pattern(None, basename):
            yield name
        return
    if has_magic(dirname):
        dirs = _glob_simple(dirname)
    else:
        dirs = [dirname]
    if has_magic(basename):
        glob_in_dir = _listdir_pattern
    else:
        glob_in_dir = _listdir_basename
    for dirname in dirs:
        for name in glob_in_dir(dirname, basename):
            yield os.path.join(dirname, name)


def _rglob(pattern, dirbase):
    """Recursively walk dirbase and yield pattern matches"""
    result = []
    dirnames, filenames = default_storage.listdir(dirbase)
    for fname in filenames:
        if fnmatch.fnmatch(fname, pattern):
            result.append(os.path.join(dirbase, fname))
    for dirn in dirnames:
        result.extend(_rglob(pattern, os.path.join(dirbase, dirn)))
    return result


def _listdir_pattern(dirname, pattern):
    try:
        directories, files = default_storage.listdir(dirname)
        names = directories + files
    except Exception:
        # We are not sure that dirname is a real directory
        # and storage implementations are really exotic.
        return []
    if pattern[0] != '.':
        names = filter(lambda x: x[0] != '.', names)
    return fnmatch.filter(names, pattern)


def _listdir_basename(dirname, basename):
    if default_storage.exists(os.path.join(dirname, basename)):
        return [basename]
    return []


magic_check = re.compile('[*?[]')


def has_magic(s):
    return magic_check.search(s) is not None
