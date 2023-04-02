# -*- mode: python -*-

block_cipher = None


a = Analysis(['./main.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

a.datas += Tree('assets', prefix='assets')

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

# enable this to see verbose output
# options = [ ('v', None, 'OPTION')]
exe = EXE(pyz,
          a.scripts,
          # options,
          exclude_binaries=True,
          name='tdp',
          debug=False, # set this to True for debug output
          strip=False,
          upx=True,
          console=True ) # set this to False this to remove the console
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='tdp')
