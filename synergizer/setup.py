"""One-time setup adapter. Never distributes the paid Synergy engine."""
import datetime, json, os, pathlib, shutil, subprocess, sys
from .backend import atomic, config, run, powershell, app_command, WINDOWS

def setup(b,role,screen,addresses,desk=None):
    if not b.core.exists():raise RuntimeError('Install and activate Synergy 3 before setting up sharing.')
    if not (b.original/'synergy-core.conf').exists():raise RuntimeError('Open Synergy once and complete its initial setup first.')
    if role=='server':
        desk=desk or b.import_existing()
        if not desk.computers:
            from .model import Desk,Computer
            desk=Desk([Computer(screen,'My desktop',primary=True)])
        for computer in desk.computers:
            if computer.primary:computer.screen=screen
        compiled=desk.compile()
    backup=b.data/'setup-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
    shutil.copytree(b.original,backup/'original')
    if b.custom.exists():shutil.copytree(b.custom,backup/'custom')
    b.custom.mkdir(parents=True,exist_ok=True)
    c=config(b.original/'synergy-core.conf')
    if c.get('security','tlsEnabled',fallback='false')!='true':raise RuntimeError('Enable encryption in Synergy before setting up sharing.')
    c['core']['computerName']=screen;c['core']['coreMode']='2' if role=='server' else '1';c['core']['processMode']='1'
    if role=='server':
        c['server']={'externalConfig':'true','externalConfigFile':str(b.layout).replace('\\','/')}
        atomic(b.layout,compiled)
        atomic(b.profile,json.dumps(desk.to_dict(),indent=2))
    else:
        if not addresses:raise RuntimeError('Enter the desktop address first.')
        c['client']['remoteHost']='"'+','.join(addresses)+'"'
    with (b.custom/'core.conf').open('w') as f:c.write(f,space_around_delimiters=False)
    if not (b.custom/'tls').exists() and (b.original/'tls').exists():shutil.copytree(b.original/'tls',b.custom/'tls')
    local=json.loads((b.original/'local.json').read_text());local.setdefault('local_system',{})['core_enabled']=False
    atomic(b.original/'local.json',json.dumps(local,indent=2))
    cmd=app_command()+['--supervise']
    if WINDOWS:
        # Per-user interactive task: no administrator/system input service is needed.
        exe=cmd[0].replace("'","''");args=subprocess.list2cmdline(cmd[1:]).replace("'","''")
        powershell(f"""Get-Process -Name synergy-service,synergy-tray -ErrorAction SilentlyContinue | Stop-Process -Force
$t=Get-ScheduledTask -TaskName 'Synergy Fixed Desktop' -ErrorAction SilentlyContinue
if ($t) {{Stop-ScheduledTask -InputObject $t; Disable-ScheduledTask -InputObject $t | Out-Null}}
Get-Process -Name synergy-core -ErrorAction SilentlyContinue | Stop-Process -Force
$a=New-ScheduledTaskAction -Execute '{exe}' -Argument '{args}'
$u=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$p=New-ScheduledTaskPrincipal -UserId $u -LogonType Interactive -RunLevel Limited
$s=New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'Synergizer Sharing' -Action $a -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $u) -Principal $p -Settings $s -Force | Out-Null
Start-ScheduledTask -TaskName 'Synergizer Sharing'""")
    else:
        import shlex
        run(['systemctl','--user','stop','synergy-3.service'],timeout=20) if subprocess.run(['systemctl','--user','is-active','--quiet','synergy-3.service']).returncode==0 else None
        unit=b.home/'.config/systemd/user/synergy-dualboot.service';unit.parent.mkdir(parents=True,exist_ok=True)
        atomic(unit,'[Unit]\nDescription=Synergizer keyboard and mouse\nPartOf=graphical-session.target\nAfter=graphical-session.target\n[Service]\nExecStart='+shlex.join(cmd)+'\nRestart=always\nRestartSec=5\nTimeoutStopSec=15\n')
        auto=b.home/'.config/autostart';auto.mkdir(parents=True,exist_ok=True)
        for name in ('synergy.desktop','synergy-3.desktop'):atomic(auto/name,'[Desktop Entry]\nType=Application\nName=Synergy managed startup\nHidden=true\n')
        atomic(auto/'synergizer-sharing.desktop','[Desktop Entry]\nType=Application\nName=Synergizer keyboard and mouse\nExec='+shlex.join(app_command()+['--session-start'])+'\nTerminal=false\n')
        run(['systemctl','--user','daemon-reload']);run(['systemctl','--user','import-environment',*[k for k in ('DISPLAY','XAUTHORITY','WAYLAND_DISPLAY','XDG_SESSION_TYPE') if k in os.environ]])
        run(['systemctl','--user','restart','synergy-dualboot.service'])
    return 'Sharing configured. Original settings backed up to '+str(backup)
