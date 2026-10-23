#!/usr/bin/env python3
import hashlib,os,pathlib,shutil,subprocess,sys,zipfile,tarfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean',str(ROOT/'packaging/Synergizer.spec')],cwd=ROOT,check=True)
bundle=ROOT/'dist/Synergizer'
shutil.copy2(ROOT/'README.md',bundle/'README.md');shutil.copy2(ROOT/'LICENSE',bundle/'LICENSE.txt')
licenses=bundle/'THIRD-PARTY-LICENSES';licenses.mkdir(exist_ok=True)
import PySide6
qtpath=pathlib.Path(PySide6.__file__).parent
for origin in [qtpath/'licenses',qtpath/'Qt/licenses',pathlib.Path('/usr/share/licenses/python3-pyside6'),pathlib.Path('/usr/share/licenses/qt6-qtbase')]:
 if origin.is_dir():shutil.copytree(origin,licenses/origin.parent.name.replace('/', '_'),dirs_exist_ok=True)
shutil.copy2(ROOT/'THIRD_PARTY.md',licenses/'NOTICE.md')
if os.name=='nt':
 (bundle/'Install Synergizer.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\nSynergizer.exe --install\r\npause\r\n')
 archive=ROOT/'dist/Synergizer-0.1.0-Windows-x64.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in bundle.rglob('*'):
   if p.is_file():z.write(p,p.relative_to(bundle.parent))
else:
 installer=bundle/'install.sh';installer.write_text('#!/bin/sh\nset -eu\ncd "$(dirname "$0")"\n./Synergizer --install\n');installer.chmod(0o755)
 archive=ROOT/'dist/Synergizer-0.1.0-Linux-x64.tar.gz'
 with tarfile.open(archive,'w:gz') as t:t.add(bundle,arcname='Synergizer')
archive.with_suffix(archive.suffix+'.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print('Ready to share:',archive)
