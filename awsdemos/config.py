# -*- coding: utf-8 -*-
from ConfigObject import config_module
import sys
import os

filename = os.path.abspath(sys.argv[-1])

if not filename.endswith('.ini'):
    filename = os.path.join(
            os.path.abspath(__file__).split('awsdemos')[0],
            'aws.demos.ini'
        )


if not os.path.isfile(filename):
    raise OSError('Cant find a valid config file')

config = config_module(__name__, __file__, filename,
                      here=os.path.dirname(filename))

