import json
from pathlib import Path

def remote_script(screen,addresses,fingerprint):
    supervisor=(Path(__file__).with_name('supervisor.py')).read_text()
    payload=json.dumps({'screen':screen,'addresses':addresses,'fingerprint':fingerprint,'supervisor':supervisor})
    return 'PAYLOAD='+repr(payload)+'\n'+r'''
import json, pathlib, os, configparser, shutil, datetime, subprocess, signal, time, sys
p=json.loads(PAYLOAD);h=pathlib.Path.home();original=h/'.config/Synergy';custom=h/'.config/Synergy-DualBoot'
if not pathlib.Path('/opt/Synergy/synergy-core').exists():raise RuntimeError('Install and activate Synergy 3 on this Linux computer first.')
if not (original/'synergy-core.conf').exists():raise RuntimeError('Open Synergy once and complete its setup first.')
legacy=(custom/'linux-setup.py').exists()
c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(custom/'core.conf' if (custom/'core.conf').exists() else original/'synergy-core.conf')
if c.get('security','tlsEnabled',fallback='false')!='true':raise RuntimeError('Enable encryption in Synergy before pairing.')
backup=h/'.local/share/Synergizer/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True,mode=0o700)
shutil.copytree(original,backup/'original')
if custom.exists():shutil.copytree(custom,backup/'custom')
custom.mkdir(parents=True,exist_ok=True);custom.chmod(0o700)
if not (custom/'tls').exists() and (original/'tls').exists():shutil.copytree(original/'tls',custom/'tls')
(custom/'tls').mkdir(exist_ok=True)
trust=custom/'tls/trusted-servers';lines=trust.read_text().splitlines() if trust.exists() else []
entry='v2:sha256:'+p['fingerprint']
if entry not in lines:lines.append(entry)
trust.write_text('\n'.join(lines)+'\n')
c['core']['computerName']=p['screen'];c['core']['coreMode']='1';c['core']['processMode']='1'
c['client']['remoteHost']='"'+','.join(p['addresses'])+'"';c['client']['dynamicConnectionRetry']='false'
with (custom/'core.conf').open('w') as f:c.write(f,space_around_delimiters=False)
(custom/'supervisor.py').write_text(p['supervisor'])
# A source-only entrypoint keeps the receiving laptop independent of Qt.
(custom/'run-client.py').write_text("from supervisor import supervise\nfrom pathlib import Path\nsupervise('/opt/Synergy/synergy-core',Path(__file__).with_name('core.conf'),'client')\n")
env=os.environ.copy();env['XDG_RUNTIME_DIR']=f'/run/user/{os.getuid()}';env['DBUS_SESSION_BUS_ADDRESS']=f'unix:path={env["XDG_RUNTIME_DIR"]}/bus'
for directory in pathlib.Path('/proc').iterdir():
 try:
  if directory.stat().st_uid!=os.getuid():continue
  args=(directory/'cmdline').read_bytes().split(b'\0')
  if args[0] in (b'/opt/Synergy/synergy-core',b'xfce4-session',b'mate-session',b'/usr/bin/gnome-session-binary'):
   for x in (directory/'environ').read_bytes().split(b'\0'):
    if b'=' in x:
     k,v=x.decode().split('=',1)
     if k in ('DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','XDG_SESSION_TYPE'):env[k]=v
 except (OSError,ValueError):pass
if not env.get('DISPLAY') and not env.get('WAYLAND_DISPLAY'):raise RuntimeError('Sign in to this laptop locally before configuring it.')
def ctl(*args):return subprocess.run(['systemctl','--user',*args],env=env,check=True)
if legacy:
 ctl('restart','synergy-dualboot.service');print('Existing client updated; recovery and tray controls preserved. Backup: '+str(backup));sys.exit(0)
subprocess.run(['systemctl','--user','stop','synergy-3.service','synergy-dualboot.service'],env=env,check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
# Stop only Synergy's managed controller and engine for the current user.
for d in pathlib.Path('/proc').iterdir():
 try:
  if d.stat().st_uid==os.getuid() and (d/'cmdline').read_bytes().split(b'\0')[0] in (b'/opt/Synergy/synergy-service',b'/opt/Synergy/synergy-tray',b'/opt/Synergy/synergy-core'):os.kill(int(d.name),signal.SIGTERM)
 except (OSError,ValueError):pass
local=json.loads((original/'local.json').read_text());local.setdefault('local_system',{})['core_enabled']=False;(original/'local.json').write_text(json.dumps(local,indent=2))
unit=h/'.config/systemd/user';unit.mkdir(parents=True,exist_ok=True)
(unit/'synergy-dualboot.service').write_text(f'[Unit]\nDescription=Synergizer sharing client\nPartOf=graphical-session.target\nAfter=graphical-session.target\n[Service]\nExecStart=/usr/bin/python3 {custom}/run-client.py\nRestart=always\nRestartSec=5\nTimeoutStopSec=15\n')
(custom/'session-start.py').write_text("import os,subprocess\nkeys=[k for k in ('DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','XDG_SESSION_TYPE') if k in os.environ]\nsubprocess.run(['systemctl','--user','import-environment',*keys],check=True)\nsubprocess.run(['systemctl','--user','restart','synergy-dualboot.service'],check=True)\n")
auto=h/'.config/autostart';auto.mkdir(parents=True,exist_ok=True)
for existing in list(auto.glob('*synergy*.desktop'))+[auto/'synergy-3.desktop']:
 existing.write_text('[Desktop Entry]\nType=Application\nName=Synergy managed startup\nHidden=true\n')
(auto/'synergizer-sharing.desktop').write_text(f'[Desktop Entry]\nType=Application\nName=Synergizer keyboard and mouse\nExec=/usr/bin/python3 {custom}/session-start.py\nTerminal=false\n')
ctl('daemon-reload');ctl('import-environment',*[k for k in ('DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','XDG_SESSION_TYPE') if k in env]);ctl('restart','synergy-dualboot.service')
print('Client configured. Backup: '+str(backup))
'''
