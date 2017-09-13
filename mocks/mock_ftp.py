
from foscambackup.constant import Constant
import foscambackup.helper as helper
from ftplib import error_perm


def delete(path):
    return True

def rmd(path):
    return True

track = []
def rmd_raise(path):
    if path.count(helper.sl()) == 4 and not path in track:
        track.append(path)
        raise error_perm("550")
    return True

def mlsd(*args, **kwargs):
    if args[0] == "/":
        yield (".", {'type': 'dir'})
        yield (Constant.sd_rec, {'type': 'dir'})
    else:
        yield (".", {'type': 'dir'})
        yield ("..", {'type': 'dir'})
        if args[0] == "/IPCamera/FXXXXX_CEEEEEEEEEEE/snap":
            yield ("20170101", {'type': 'dir'})
            yield ("20170102", {'type': 'dir'})
            yield ("20170103", {'type': 'dir'})
            yield ("20170104", {'type': 'dir'})
            yield (helper.get_current_date(), {'type': 'dir'})
        if args[0].count(helper.sl()) == 5:
            dirname = args[0].split(helper.sl())[5]
            yield (dirname + ".jpg", {'type': 'file'})
        elif args[0].count(helper.sl()) == 4:
            dirname = args[0].split(helper.sl())[4]
            yield (dirname + "-120000", {'type': 'dir'})
            yield (dirname + "-140000", {'type': 'dir'})
            yield (dirname + "-160000", {'type': 'dir'})
            yield (dirname + "-170000", {'type': 'dir'})
    