######################################################################
##
##   Copyright (c) 2013 Tavendo GmbH. All rights reserved.
##   Author(s): Tobias Oberstein
##
######################################################################

a = Analysis(['exe_webmq.py'],
             pathex = ['/home/webmq/scm/WebMQ/appliance/exe'],
             hiddenimports = [],
             hookspath = None)

pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name = os.path.join('dist', 'webmq'),
          debug = False,
          strip = None,
          upx = True,
          console = True ,
          icon = 'tavendo.ico')
