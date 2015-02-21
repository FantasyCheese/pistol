# -*- mode: python -*-
a = Analysis(['poeshop.py'],
             pathex=['D:\\Programming\\Python\\POEShop'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='pistol.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
			   Tree('data', prefix='data'),
               strip=None,
               upx=True,
               name='pistol')
