from pathlib import Path
root=Path(SPEC).resolve().parents[1]
a=Analysis([str(root/'launch.py')],pathex=[str(root)],binaries=[],datas=[(str(root/'synergizer/assets'),'synergizer/assets'),(str(root/'synergizer/supervisor.py'),'synergizer')],hiddenimports=["paramiko"],hookspath=[],excludes=['PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtQml','PySide6.QtQuick','tkinter'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='Synergizer',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False,icon=str(root/'synergizer/assets/synergizer.ico'))
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='Synergizer')
