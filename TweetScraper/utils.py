import os

def mkdirs(dirs):
    ''' Create `dirs` if not exist. '''
    if not os.path.exists(dirs):
        os.makedirs(dirs)