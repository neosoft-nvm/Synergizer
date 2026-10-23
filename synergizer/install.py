"""User-level installation and desktop shortcuts; never requires root."""
import os,pathlib,shutil,subprocess,sys,uuid
from .backend import Backend,WINDOWS,atomic,run

def install_user():
    if not getattr(sys,'frozen',False):raise RuntimeError('Use a packaged Synergizer build to install desktop shortcuts.')
    b=Backend();source=pathlib.Path(sys.executable).parent;dest=b.data/'app'
    if source.resolve()!=dest.resolve():
        # Keep user profiles/backups outside app/ so replacing the application is safe.
        stage=b.data/('app.new-'+uuid.uuid4().hex[:8]);previous=b.data/'app.previous'
        shutil.copytree(source,stage)
        if previous.exists():shutil.rmtree(previous)
        try:
            if dest.exists():dest.rename(previous)
            try:stage.rename(dest)
            except Exception:
                if previous.exists():previous.rename(dest)
                raise
        except Exception:
            shutil.rmtree(stage,ignore_errors=True);raise
        shutil.rmtree(previous,ignore_errors=True)
    exe=dest/pathlib.Path(sys.executable).name
    assets=dest/'_internal/synergizer/assets'
    if WINDOWS:
        icon=assets/'synergizer.ico'
        desktop=pathlib.Path(subprocess.check_output(['powershell.exe','-NoProfile','-Command',"[Environment]::GetFolderPath('Desktop')"],text=True).strip())
        start=pathlib.Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs';start.mkdir(parents=True,exist_ok=True)
        def escape(s):return str(s).replace("'","''")
        from .backend import powershell
        for target in [desktop/'Synergizer.lnk',start/'Synergizer.lnk']:
            powershell(f"$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut('{escape(target)}');$s.TargetPath='{escape(exe)}';$s.IconLocation='{escape(icon)}';$s.WorkingDirectory='{escape(dest)}';$s.Save()")
    else:
        exe.chmod(0o755);icons=b.home/'.local/share/icons/hicolor/scalable/apps';icons.mkdir(parents=True,exist_ok=True);shutil.copy2(assets/'synergizer.svg',icons/'synergizer.svg')
        applications=b.home/'.local/share/applications';applications.mkdir(parents=True,exist_ok=True)
        entry='[Desktop Entry]\nType=Application\nName=Synergizer\nComment=Arrange your computers and recover keyboard sharing\nExec="'+str(exe)+'"\nIcon=synergizer\nTerminal=false\nCategories=Utility;Settings;\nStartupWMClass=Synergizer\n'
        target=applications/'synergizer.desktop';atomic(target,entry);target.chmod(0o755)
        try:desktop=pathlib.Path(run(['xdg-user-dir','DESKTOP']))
        except Exception:desktop=b.home/'Desktop'
        desktop.mkdir(parents=True,exist_ok=True);shutil.copy2(target,desktop/'Synergizer.desktop')
        if shutil.which('update-desktop-database'):subprocess.run(['update-desktop-database',str(applications)],capture_output=True)
        # Pull the shared desk before the existing engine starts on the next boot.
        if (b.custom/'core.conf').exists():
            drop=b.home/'.config/systemd/user/synergy-dualboot.service.d';drop.mkdir(parents=True,exist_ok=True)
            atomic(drop/'synergizer-sync.conf','[Service]\nExecStartPre="'+str(exe)+'" --sync\n')
            subprocess.run(['systemctl','--user','daemon-reload'],capture_output=True)
    print('Installed Synergizer and desktop/application-menu shortcuts at '+str(exe))
    return str(exe)
