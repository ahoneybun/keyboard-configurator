import os
import re
import shutil
import subprocess
import sys

# Paths to find executables and libraries
RUSTUP = f"{os.environ['HOMEPATH']}/.cargo/bin/rustup.exe"
WIX = "C:/Program Files (x86)/WiX Toolset v3.11"
# Rust toolchain version to use
RUST_TOOLCHAIN = 'stable-i686-pc-windows-gnu'
# Executables to install
DEBUG = '--debug' in sys.argv
TARGET_DIR = f"../target/{'debug' if DEBUG else 'release'}"
EXES = {
    f"{TARGET_DIR}/examples/keyboard_color.exe",
}

DLL_RE = r"(?<==> ).*\\mingw32\\bin\\(\S+.dll)"


# Use ntldd to find the mingw dlls required by a .exe
def find_depends(exe):
    output = subprocess.check_output(['ntldd.exe', '-R', exe], universal_newlines=True)
    dlls = set()
    for l in output.splitlines():
        m = re.search(DLL_RE, l, re.IGNORECASE)
        if m:
            dlls.add((m.group(0), m.group(1)))
    return dlls


# Build application with rustup
cmd = [RUSTUP, 'run', RUST_TOOLCHAIN, 'cargo', 'build', '--examples']
if not DEBUG:
    cmd.append('--release')
subprocess.call(cmd)

# Generate set of all required dlls
dlls = set()
for i in EXES:
    dlls = dlls.union(find_depends(i))

# Generate libraries.wxi
with open('libraries.wxi', 'w') as f:
    f.write("<!-- Generated by build.py -->\n")
    f.write('<Include>\n')

    for _, i in dlls:
        id_ = i.replace('.dll', '').replace('-', '_').replace('+', '')
        f.write(f"    <File Name='{i}' DiskId='1' Source='out/{i}' />\n")

    f.write('</Include>\n')

# Copy executables and libraries
if os.path.exists('out'):
    shutil.rmtree('out')
os.mkdir('out')
for i in EXES:
    filename = i.split('/')[-1]
    print(f"Strip {i} -> out/{filename}")
    subprocess.call([f"strip.exe", '-o', f"out/{filename}", i])
for src, filename in dlls:
    print(f"Copy {src} -> out/{filename}")
    shutil.copy(f"{src}", 'out')

# Build .msi
subprocess.call([f"{WIX}/bin/candle.exe", ".\keyboard-configurator.wxs"])
subprocess.call([f"{WIX}/bin/light.exe", "-ext", "WixUIExtension", ".\keyboard-configurator.wixobj"])