# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata
import os

# Include logo and mute icon
datas = [('logo.png', '.'), ('mute.png', '.')]

# Include the entire ffmpeg essentials folder
ffmpeg_dir = 'ffmpeg-2025-11-10-git-133a0bcb13-essentials_build'
if os.path.exists(ffmpeg_dir):
    # Add the bin directory with ffmpeg executables
    datas.append((os.path.join(ffmpeg_dir, 'bin'), os.path.join(ffmpeg_dir, 'bin')))
    # Add the LICENSE and README for compliance
    datas.append((os.path.join(ffmpeg_dir, 'LICENSE'), ffmpeg_dir))
    datas.append((os.path.join(ffmpeg_dir, 'README.txt'), ffmpeg_dir))

binaries = []
hiddenimports = ['tkinterdnd2', 'moviepy', 'moviepy.editor', 'moviepy.video.io.VideoFileClip', 'moviepy.video.compositing.CompositeVideoClip', 'moviepy.video.VideoClip', 'moviepy.audio.AudioClip', 'PIL', 'PIL.Image', 'imageio_ffmpeg', 'subprocess']
datas += copy_metadata('imageio-ffmpeg')
binaries += collect_dynamic_libs('imageio_ffmpeg')
tmp_ret = collect_all('moviepy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('tkinterdnd2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('imageio_ffmpeg')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['Hashbrown.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Hashbrown',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.png'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Hashbrown',
)
