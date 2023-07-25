

import os
import hashlib

def wipe_dir( path="effects",sub=True):
    print( "wipe path {}".format(path) )
    try:
        l = os.listdir(path)
        for f in l:
            child = "{}/{}".format(path, f)
            st = os.stat(child)
            if st[0] & 0x4000:  # stat.S_IFDIR
                if sub:
                    wipe_dir(child,sub)
                    try:
                        os.rmdir(child)
                    except:
                        print("Error deleting folder {}".format(child))
            else: # File
                try:  
                    os.remove(child)
                except:
                    print("Error deleting file {}".format(child))
    except:
        print("file not found, probably")

def hash(fname):
    try:
        file = open(fname, "rb")
        hash = hashlib.sha256()
        chunk = file.read(256)
        while len(chunk):
            hash.update(chunk)
            chunk = file.read(256)
        file.close()
        return hash.digest()
    except Exception as e:
        import sys
        sys.print_exception(e)
        print(fname, "not found for hashing or error")
        return b''


def filelist(path="."):
    result = []
    l = os.listdir(path)
    for f in l:
        child = "{}/{}".format(path, f)
        st = os.stat(child)
        if st[0] & 0x4000:  # stat.S_IFDIR
            result += filelist(child)
        else:
            result.append((child, hash(child)))
    return result


def hash_dirlist(dir):
    try:
        dirlist = filelist(dir)
        dirlist = [x[0] for x in dirlist]
        dirlist.sort()
        hash = hashlib.sha256("\n".join(dirlist))
        return hash.digest()
    except Exception as e:
        import sys
        sys.print_exception(e)
        print(dir, "not found for hashing or error")
        return b''
    
def ensure_path_exists(file):
    dirs = file.split("/")[:-1]

    for i in range(len(dirs)):
        dir = "/".join(dirs[:i+1])
        try:
            os.mkdir(dir)
        except:
            pass