import asyncio
import functools
from unittest import mock as utm
import hashlib

import arrow
from pyfakefs import fake_filesystem as ffs


class PathMock(utm.Mock):

    def __init__(self, fs=None, *pathsegments, **kwargs):
        super(PathMock, self).__init__()

        self._fs = fs
        self._path = self._fs.JoinPaths(*pathsegments)

    def iterdir(self):
        fake_os = ffs.FakeOsModule(self._fs)
        for child in fake_os.listdir(self._path):
            yield PathMock(self._fs, self._path, child)

    def stat(self):
        fake_os = ffs.FakeOsModule(self._fs)
        return fake_os.stat(self._path)

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        fake_os = ffs.FakeOsModule(self._fs)
        try:
            fake_os.makedirs(self._path)
        except OSError as e:
            # iDontCare
            pass
        return True

    def is_file(self):
        fake_os = ffs.FakeOsModule(self._fs)
        return fake_os.path.isfile(self._path)

    def is_dir(self):
        fake_os = ffs.FakeOsModule(self._fs)
        return fake_os.path.isdir(self._path)

    def unlink(self):
        fake_os = ffs.FakeOsModule(self._fs)
        return fake_os.unlink(self._path)

    def open(self, mode):
        fake_open = ffs.FakeFileOpen(self._fs)
        return fake_open(self._path, mode)

    def __truediv__(self, name):
        return PathMock(self._fs, self._path, name)

    def __str__(self):
        return self._path


class NodeMock(utm.Mock):

    def __init__(self, fs, path, *args, **kwargs):
        super(NodeMock, self).__init__()

        self._fs = fs
        self._path = path

    @property
    def name(self):
        dirname, basename = self._fs.SplitPath(self._path)
        return basename

    @property
    def modified(self):
        f = self._fs.GetObject(self._path)
        return arrow.fromtimestamp(f.st_mtime).replace(tzinfo='local')

    @property
    def trashed(self):
        return False

    @property
    def is_folder(self):
        fake_os = ffs.FakeOsModule(self._fs)
        return fake_os.path.isdir(self._path)

    @property
    def size(self):
        fake_os = ffs.FakeOsModule(self._fs)
        return fake_os.path.getsize(self._path)

    @property
    def md5(self):
        fake_open = ffs.FakeFileOpen(self._fs)
        return get_md5(fake_open, self._path)


def create_async_mock(return_value=None):
    loop = asyncio.get_event_loop()
    f = loop.create_future()
    f.set_result(return_value)
    return utm.Mock(return_value=f)


def create_fake_local_file_system():
    fs = ffs.FakeFilesystem()
    file_1 = fs.CreateFile('/local/file_1.txt', contents='file 1')
    file_1.st_mtime = 1467800000
    file_2 = fs.CreateFile('/local/folder_1/file_2.txt', contents='file 2')
    file_2.st_mtime = 1467801000
    folder_1 = fs.GetObject('/local/folder_1')
    folder_1.st_mtime = 1467802000
    return fs


def create_fake_remote_file_system():
    fs = ffs.FakeFilesystem()
    file_3 = fs.CreateFile('/remote/file_3.txt', contents='file 3')
    file_3.st_mtime = 1467803000
    file_4 = fs.CreateFile('/remote/folder_2/file_4.txt', contents='file 4')
    file_4.st_mtime = 1467804000
    folder_2 = fs.GetObject('/remote/folder_2')
    folder_2.st_mtime = 1467805000
    return fs


def get_md5(open_, path):
    hasher = hashlib.md5()
    with open_(path, 'rb') as fin:
        while True:
            chunk = fin.read(65536)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()
