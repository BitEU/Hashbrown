# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata
import os

# Include logo and mute icon
datas = [('logo.png', '.'), ('mute.png', '.'), ('mute_2.png', '.')]

# NOTE: We don't bundle ffmpeg manually - imageio_ffmpeg already includes it!
# This saves ~290 MB by avoiding duplication

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
    excludes=['scipy', 'matplotlib', 'pandas', 'IPython', 'jupyter', 'notebook', 
              'setuptools', 'distutils', 'lxml', 'pytest', 'tests', 'test',
              'pydoc', 'pydoc_data', 'doctest', 'xmlrpc',
              'unittest', 'pkg_resources',  # Not needed for this app
              # Exclude PIL image codecs you don't use
              'PIL.AvifImagePlugin', 'PIL.BlpImagePlugin', 'PIL.BmpImagePlugin',
              'PIL.BufrStubImagePlugin', 'PIL.CurImagePlugin', 'PIL.DcxImagePlugin',
              'PIL.DdsImagePlugin', 'PIL.EpsImagePlugin', 'PIL.FitsImagePlugin',
              'PIL.FliImagePlugin', 'PIL.FpxImagePlugin', 'PIL.FtexImagePlugin',
              'PIL.GbrImagePlugin', 'PIL.GifImagePlugin', 'PIL.GribStubImagePlugin',
              'PIL.Hdf5StubImagePlugin', 'PIL.IcnsImagePlugin', 'PIL.IcoImagePlugin',
              'PIL.ImImagePlugin', 'PIL.ImtImagePlugin', 'PIL.IptcImagePlugin',
              'PIL.Jpeg2KImagePlugin', 'PIL.McIdasImagePlugin', 'PIL.MicImagePlugin',
              'PIL.MpegImagePlugin', 'PIL.MpoImagePlugin', 'PIL.MspImagePlugin',
              'PIL.PalmImagePlugin', 'PIL.PcdImagePlugin', 'PIL.PcxImagePlugin',
              'PIL.PixarImagePlugin', 'PIL.PpmImagePlugin', 'PIL.PsdImagePlugin',
              'PIL.QoiImagePlugin', 'PIL.SgiImagePlugin', 'PIL.SpiderImagePlugin',
              'PIL.SunImagePlugin', 'PIL.TgaImagePlugin', 'PIL.WalImagePlugin',
              'PIL.WebPImagePlugin', 'PIL.WmfImagePlugin', 'PIL.XbmImagePlugin',
              'PIL.XpmImagePlugin', 'PIL.XVThumbImagePlugin'],
    noarchive=False,
    optimize=0,  # numpy has issues with optimize=2
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
    upx=False,  # UPX not installed - install from https://upx.github.io/ for additional ~30% compression
    upx_exclude=[],
    name='Hashbrown',
)
