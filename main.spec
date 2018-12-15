# -*- mode: python -*-
import sys

a = Analysis(['main.py'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          # Static link the Visual C++ Redistributable DLLs if on Windows
          a.binaries,
          a.zipfiles,
          a.datas,
          name='coinz',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon='mao.ico')
