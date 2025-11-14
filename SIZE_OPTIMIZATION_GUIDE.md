# Hashbrown Size Optimization Guide

## Problem
The compiled distribution was ~467 MB - way too large for a simple video muter!

## What Was Taking Up Space?

### Before Optimization:
- **FFmpeg folder: 290 MB** - Bundled the entire "essentials" build including:
  - ffmpeg.exe (needed) ✓
  - ffplay.exe (not needed) ✗
  - ffprobe.exe (not needed) ✗
  - Entire `doc/` folder with HTML documentation (not needed) ✗
  
- **imageio_ffmpeg: 84 MB** - MoviePy's bundled FFmpeg (duplicate!)
- **Python libraries: ~93 MB** - Including debugging tools, test modules, etc.

### Total: ~467 MB

## Optimizations Applied

### 1. ✅ Bundle Only ffmpeg.exe (~100 MB saved)
Changed from bundling the entire FFmpeg folder to just `ffmpeg.exe`:
```python
# OLD: Bundle entire bin folder
datas.append((os.path.join(ffmpeg_dir, 'bin'), ...))

# NEW: Bundle only ffmpeg.exe
datas.append((ffmpeg_exe, os.path.join(ffmpeg_dir, 'bin')))
```

### 2. ✅ Exclude imageio_ffmpeg (~84 MB saved)
Since we're bundling our own FFmpeg, we don't need MoviePy's bundled version:
```python
# Removed these lines:
# datas += copy_metadata('imageio-ffmpeg')
# binaries += collect_dynamic_libs('imageio_ffmpeg')
# tmp_ret = collect_all('imageio_ffmpeg')
```

### 3. ✅ Exclude Unnecessary Python Modules (~20-30 MB saved)
Added excludes for modules not needed in production:
- `pytest`, `unittest`, `test` - Testing frameworks
- `pydoc`, `pdb`, `bdb` - Documentation and debugging tools
- `email`, `ftplib`, `http` - Network modules not used
- `matplotlib`, `scipy` - Heavy scientific libraries (if detected)

### 4. ✅ Enable Bytecode Optimization (~5-10 MB saved)
```python
optimize=2  # Remove docstrings and optimize bytecode
noarchive=False  # Compress Python bytecode into PYZ archive
```

### 5. ✅ Enable UPX Compression (~30-50 MB saved)
Compresses executables and DLLs:
```python
upx=True
upx_exclude=['python314.dll', 'tcl86t.dll', 'tk86t.dll']
```
Note: Some DLLs crash when compressed with UPX, so we exclude them.

## Expected Results

### After Optimization:
- **FFmpeg: ~50 MB** (just the exe, compressed)
- **Python libraries: ~60 MB** (optimized and compressed)
- **Numpy/PIL: ~30 MB** (compressed)
- **Other: ~20 MB**

### **New Total: ~160-200 MB** (60-70% reduction!)

## To Rebuild with Optimizations

1. **Install UPX (optional but recommended):**
   ```powershell
   # Download from: https://github.com/upx/upx/releases
   # Or via Chocolatey:
   choco install upx
   ```

2. **Rebuild:**
   ```powershell
   pyinstaller Hashbrown.spec
   ```

3. **Check the size:**
   ```powershell
   Get-ChildItem -Path "dist\Hashbrown" -Recurse | 
   Measure-Object -Property Length -Sum | 
   Select-Object @{Name="Size(MB)";Expression={[math]::Round($_.Sum/1MB,2)}}
   ```

## Alternative: One-File Executable

If you want an even smaller distribution (single .exe file):

1. Change the spec file back to one-file mode
2. FFmpeg will be extracted to temp at runtime
3. Slightly slower startup, but easier to distribute
4. Size will be similar due to compression

To do this:
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Hashbrown',
    ...
    upx=True,
)
# Remove the COLLECT section
```

## Further Optimizations (Advanced)

### Use FFmpeg Shared Build Instead of Static
- Static builds include all codecs (~50 MB)
- Shared builds use DLLs (~30 MB total)
- More complex to bundle but smaller

### Use Minimal Python Build
- PyInstaller includes entire Python runtime
- Could use embedded Python for smaller size
- Much more complex to set up

### Bundle Python Modules as .pyc Only
- Already done with `optimize=2`
- Removes all source code and docstrings

## Trade-offs

### Size vs Compatibility
- Smaller = more compression = slightly slower startup
- UPX can cause false positives in some antivirus software
- One-folder is more compatible but larger uncompressed

### Size vs Features
- Could remove moviepy and use pure FFmpeg (saves ~50 MB)
- Would require rewriting video processing logic
- Trade development time for smaller size

## Recommended Approach

**For most users: One-folder with optimizations**
- ~160-200 MB total
- Fast startup
- No antivirus issues
- Professional distribution

**For web download: 7zip compression**
- Compress the folder with 7zip
- Expect ~70-100 MB .7z file
- Users extract and run

## Distribution Size Comparison

- **Original (one-file, no optimization): ~467 MB**
- **Optimized (one-folder): ~160-200 MB**
- **7zip compressed: ~70-100 MB**
- **Installer (with compression): ~80-120 MB**

Choose based on your distribution method!
