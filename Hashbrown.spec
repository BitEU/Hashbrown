# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata
import os

# Include logo and mute icon
datas = [('logo.png', '.'), ('mute.png', '.')]

# Include ONLY the ffmpeg.exe - not the entire essentials folder
# This saves ~200+ MB by excluding ffplay.exe, ffprobe.exe, and the entire doc folder
ffmpeg_dir = 'ffmpeg-2025-11-10-git-133a0bcb13-essentials_build'
if os.path.exists(ffmpeg_dir):
    # Add ONLY ffmpeg.exe (not ffplay or ffprobe)
    ffmpeg_exe = os.path.join(ffmpeg_dir, 'bin', 'ffmpeg.exe')
    if os.path.exists(ffmpeg_exe):
        datas.append((ffmpeg_exe, os.path.join(ffmpeg_dir, 'bin')))
    # Add the LICENSE for compliance (required by FFmpeg license)
    license_file = os.path.join(ffmpeg_dir, 'LICENSE')
    if os.path.exists(license_file):
        datas.append((license_file, ffmpeg_dir))

binaries = []
hiddenimports = ['tkinterdnd2', 'moviepy', 'moviepy.editor', 'moviepy.video.io.VideoFileClip', 'moviepy.video.compositing.CompositeVideoClip', 'moviepy.video.VideoClip', 'moviepy.audio.AudioClip', 'PIL', 'PIL.Image', 'subprocess']

# Collect moviepy data and binaries
tmp_ret = collect_all('moviepy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Collect tkinterdnd2 data and binaries  
tmp_ret = collect_all('tkinterdnd2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# EXCLUDE imageio_ffmpeg entirely - we're bundling our own FFmpeg
# This saves ~84 MB by not bundling a second copy of FFmpeg


a = Analysis(
    ['Hashbrown.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'pytest', 'unittest', 'test', 'tests',
        'pydoc', 'pydoc_data',
        'xml', 'xmlrpc',
        'pdb', 'bdb', 'cmd', 'code', 'codeop',  # debugger modules
        'doctest', 'email',
        'ftplib', 'http', 'urllib3',
        'matplotlib', 'scipy',  # heavy scientific libraries if not used
        'IPython', 'jupyter',
        'imageio_ffmpeg',  # We're bundling our own FFmpeg
    ],
    noarchive=False,  # Changed to False to compress Python bytecode
    optimize=2,  # Optimize bytecode (level 2 = remove docstrings)
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
    upx=True,  # Enable UPX compression
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
    upx=True,  # Enable UPX compression for DLLs
    upx_exclude=['python314.dll', 'tcl86t.dll', 'tk86t.dll'],  # Exclude DLLs that don't compress well with UPX
    name='Hashbrown',
)
