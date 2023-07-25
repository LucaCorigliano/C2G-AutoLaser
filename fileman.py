import os
class fm:
    cwd = "."
    @staticmethod
    def set_cwd(cwd):
        fm.cwd = cwd
    @staticmethod
    def open(file, mode):
        return open(os.path.join(fm.cwd, file), mode)
    @staticmethod
    def isfile(file):
        return os.path.isfile(os.path.join(fm.cwd, file))