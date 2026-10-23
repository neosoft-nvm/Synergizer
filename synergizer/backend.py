from __future__ import annotations
import configparser, copy, datetime, hashlib, ipaddress, json, os, pathlib, platform, re, shutil, socket, subprocess, sys, tempfile, uuid
from concurrent.futures import ThreadPoolExecutor
from .model import Computer, Desk, parse_layout, SAFE_NAME

WINDOWS=os.name=='nt'
def run(args,timeout=20,input=None):
    flags=subprocess.CREATE_NO_WINDOW if WINDOWS else 0
    p=subprocess.run(args,input=input,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,creationflags=flags)
    if p.returncode:raise RuntimeError((p.stderr or p.stdout or f'Command failed ({p.returncode})').strip()[-2200:])
    return p.stdout.strip()
def powershell(script):return run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],timeout=35)
def atomic(path,data):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.synergizer-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
def config(path):
    c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(path,encoding='utf-8-sig');return c

def app_command():
    return [sys.executable] if getattr(sys,'frozen',False) else [sys.executable,'-m','synergizer']

class Backend:
    def __init__(self,data_dir=None):
        self.home=pathlib.Path.home()
        self.data=pathlib.Path(data_dir) if data_dir else (pathlib.Path(os.environ.get('LOCALAPPDATA',self.home))/'Synergizer' if WINDOWS else self.home/'.local/share/Synergizer')
        self.data.mkdir(parents=True,exist_ok=True)
        if not WINDOWS:self.data.chmod(0o700)
        self.original=pathlib.Path(os.environ.get('PROGRAMDATA','C:/ProgramData'))/'Synergy/config' if WINDOWS else self.home/'.config/Synergy'
        self.custom=pathlib.Path(os.environ.get('PROGRAMDATA','C:/ProgramData'))/'Synergy-DualBoot' if WINDOWS else self.home/'.config/Synergy-DualBoot'
        self.core=pathlib.Path(os.environ.get('PROGRAMFILES','C:/Program Files'))/'Synergy/synergy-core.exe' if WINDOWS else pathlib.Path('/opt/Synergy/synergy-core')
        self.settings_file=self.data/'settings.json'
        self.settings=json.loads(self.settings_file.read_text()) if self.settings_file.exists() else {'theme':'system','shared_folder':''}
        self.profile=self.data/'desk.json';self.layout=self.custom/'layout.conf'
    def save_settings(self):atomic(self.settings_file,json.dumps(self.settings,indent=2))
    def shared(self):
        value=self.settings.get('shared_folder','');return pathlib.Path(value) if value else None
    def load(self):
        shared=self.shared()
        if shared and (shared/'desk.json').is_file():return Desk.from_dict(json.loads((shared/'desk.json').read_text()))
        if self.profile.is_file():return Desk.from_dict(json.loads(self.profile.read_text()))
        return self.import_existing()
    def import_existing(self):
        custom=config(self.custom/'core.conf');original=config(self.original/'synergy-core.conf')
        c=custom if custom.has_section('core') else original
        name=c.get('core','computerName',fallback='desktop')
        layout=self.layout if self.layout.exists() else self.original/'synergy.conf'
        if not layout.exists():return Desk()
        desk=parse_layout(layout.read_text(),name)
        # Friendly names and addresses come from the user's own installation only.
        db={};local={}
        try:db=json.loads((self.original/'db.json').read_text())['data'];local=json.loads((self.original/'local.json').read_text())
        except (OSError,KeyError,ValueError):pass
        peers=[]
        try:
            if shutil.which('tailscale'):peers=list(json.loads(run(['tailscale','status','--json'],timeout=3)).get('Peer',{}).values())
        except Exception:pass
        for comp in desk.computers:
            if comp.primary:comp.label='My desktop';comp.platform='Windows + Linux' if (self.custom.exists() and comp.screen=='desktop') else ('Windows' if WINDOWS else 'Linux')
            for item in db.get('computers',[]):
                if comp.screen.endswith(item['id'][-8:]):
                    comp.label=item.get('name',comp.label).replace('_',' ')
                    a=local.get('local_computers',{}).get(item['id'])
                    comp.addresses=[a] if a and a!='127.0.0.1' else []
                    hostname=item.get('hostname','').split('.')[0].lower()
                    if not WINDOWS and shutil.which('getent') and hostname:
                        try:
                            resolved=run(['getent','ahostsv4',hostname+'.local'],timeout=2)
                            for line in resolved.splitlines():
                                ip=line.split()[0]
                                if ip not in comp.addresses:comp.addresses.append(ip)
                        except Exception:pass
                    for peer in peers:
                        if peer.get('HostName','').lower()==hostname:
                            comp.addresses+= [ip for ip in peer.get('TailscaleIPs',[]) if ip not in comp.addresses]
        return desk
    def backup(self,reason):
        stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');dest=self.data/'backups'/stamp;dest.mkdir(parents=True)
        targets={'layout.conf':self.layout,'core.conf':self.custom/'core.conf','desk.json':self.profile}
        shared=self.shared()
        if shared:targets.update({'shared-desk.json':shared/'desk.json','shared-layout.conf':shared/'layout.conf'})
        meta={'reason':reason,'created':datetime.datetime.now().isoformat(),'files':{}}
        for name,path in targets.items():
            exists=path.exists()
            if exists:shutil.copy2(path,dest/name)
            meta['files'][name]={'path':str(path),'existed':exists}
        atomic(dest/'backup.json',json.dumps(meta,indent=2));return dest
    def list_backups(self):
        result=[]
        for p in sorted((self.data/'backups').glob('*/backup.json'),reverse=True):
            try:result.append((p.parent,json.loads(p.read_text())))
            except (OSError,ValueError):pass
        return result
    def restore_files(self,backup):
        meta=json.loads((pathlib.Path(backup)/'backup.json').read_text())
        for name,item in meta['files'].items():
            p=pathlib.Path(item['path'])
            if item['existed']:atomic(p,(pathlib.Path(backup)/name).read_text())
            elif p.exists():p.unlink()
    def restore(self,backup):
        self.backup('Before restoring a previous desk')
        self.restore_files(backup);self.restart();return self.load()
    def apply(self,desk):
        text=desk.compile()
        if not self.core.exists():raise RuntimeError('Install and activate Synergy 3 on this computer first, then return to Synergizer.')
        if not (self.custom/'core.conf').exists():raise RuntimeError('Set up sharing on this computer first using Settings → Set up sharing.')
        if config(self.custom/'core.conf').get('core','coreMode',fallback='')!='2':raise RuntimeError('Open the layout editor on the computer that shares its keyboard and mouse.')
        current_name=config(self.custom/'core.conf').get('core','computerName',fallback='')
        if next(c for c in desk.computers if c.primary).screen!=current_name:raise RuntimeError('The desktop screen name must match its installed sharing service. Edit its friendly name instead.')
        shared=self.shared()
        if shared and not shared.is_dir():raise RuntimeError('The shared Windows/Linux folder is unavailable. Mount it before applying this desk.')
        snapshot=self.backup('Before applying desk changes')
        try:
            desk.revision=uuid.uuid4().hex
            atomic(self.layout,text);atomic(self.profile,json.dumps(desk.to_dict(),indent=2))
            if shared:
                atomic(shared/'layout.conf',text);atomic(shared/'desk.json',json.dumps(desk.to_dict(),indent=2))
            self.restart()
        except Exception:
            self.restore_files(snapshot)
            try:self.restart()
            except Exception:pass
            raise
        return snapshot
    def sync(self):
        shared=self.shared()
        if shared and shared.is_dir():
            try:self.publish_identity()
            except (OSError,ValueError,configparser.Error):pass
        if shared and (shared/'desk.json').exists():
            desk=Desk.from_dict(json.loads((shared/'desk.json').read_text()));text=desk.compile()
            if not self.layout.exists() or self.layout.read_text()!=text:atomic(self.layout,text)
            atomic(self.profile,json.dumps(desk.to_dict(),indent=2))
    def local_status(self):
        if not (self.custom/'core.conf').exists():return 'Not set up'
        if WINDOWS:
            out=powershell("Get-CimInstance Win32_Process -Filter \"Name='synergy-core.exe'\" | Select-Object -ExpandProperty CommandLine")
            return 'Running' if 'Synergy-DualBoot' in out else 'Stopped'
        out=run(['systemctl','--user','is-active','synergy-dualboot.service'])
        return 'Running' if out=='active' else 'Stopped'
    def restart(self):
        if WINDOWS:
            script="""$t=Get-ScheduledTask -TaskName 'Synergizer Sharing','Synergy Fixed Desktop' -ErrorAction SilentlyContinue | Select-Object -First 1
if (!$t) { throw 'Sharing startup task not found. Use Settings > Set up sharing.' }
Stop-ScheduledTask -InputObject $t
Get-CimInstance Win32_Process -Filter "Name='synergy-core.exe'" | Where-Object {$_.CommandLine -like '*Synergy-DualBoot*'} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force}
Start-ScheduledTask -InputObject $t"""
            powershell(script)
        else:run(['systemctl','--user','restart','synergy-dualboot.service'])
        return 'Sharing restarted. Clients will reconnect automatically.'
    def logs(self):
        if WINDOWS:
            paths=[self.custom/'sharing.log',self.custom/'core.stderr.log',self.custom/'server.log'];return '\n'.join(p.read_text(errors='replace')[-16000:] for p in paths if p.exists()) or 'No sharing logs yet.'
        return run(['journalctl','--user','-u','synergy-dualboot.service','-n','100','--no-pager'])
    def status(self,desk):
        statuses={}
        try:statuses[next(c.screen for c in desk.computers if c.primary)]=self.local_status()
        except Exception:
            for c in desk.computers:
                if c.primary:statuses[c.screen]='Unavailable'
        # Socket ownership is checked on the local sharing engine, not by opening a
        # bogus TLS connection to a laptop client (clients do not listen on 24800).
        if not WINDOWS:
            try:
                tcp=run(['ss','-Htn','state','established','(','sport','=',':24800',')'])
                peers={line.split()[-1].rsplit(':',1)[0].strip('[]').removeprefix('::ffff:') for line in tcp.splitlines() if line.split()}
                for c in desk.computers:
                    if not c.primary:statuses[c.screen]='Connected' if any(a in peers for a in c.addresses) else ('Not connected' if c.addresses else 'Address needed')
            except Exception:pass
        else:
            try:
                tcp=powershell("Get-NetTCPConnection -State Established -LocalPort 24800 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty RemoteAddress")
                for c in desk.computers:
                    if not c.primary:statuses[c.screen]='Connected' if any(a in [v.removeprefix('::ffff:') for v in tcp.splitlines()] for a in c.addresses) else 'Not connected'
            except Exception:pass
        return statuses
    def discover(self,networks=()):
        found=[]
        try:
            local=json.loads((self.original/'local.json').read_text());db=json.loads((self.original/'db.json').read_text())['data']
            for d in db.get('computers',[]):
                address=local.get('local_computers',{}).get(d['id'])
                if address and address!='127.0.0.1':found.append({'label':d.get('name','Computer'),'address':address})
        except (OSError,ValueError,KeyError):pass
        candidates=set()
        for network in networks:
            try:
                net=ipaddress.ip_network(network,strict=False)
                if net.version==4 and net.num_addresses<=256:candidates.update(str(h) for h in net.hosts())
            except ValueError:pass
        def probe(a):
            try:
                with socket.create_connection((a,22),timeout=.25):return a
            except OSError:return None
        with ThreadPoolExecutor(max_workers=32) as pool:
            for a in pool.map(probe,candidates):
                if a and not any(d['address']==a for d in found):found.append({'label':'Computer with SSH available','address':a})
        return found
    def inspect_host(self,c):
        from .ssh_access import inspect_host
        if not c.addresses:raise ValueError('Enter an address in Edit first.')
        return inspect_host(c.addresses[0],self.data/'known_hosts')
    def trust_host(self,info):
        from .ssh_access import trust_host
        trust_host(info,self.data/'known_hosts')
    def authorize_remote(self,c,password=None):
        from .ssh_access import authorize
        return authorize(c,self.data,password)
    def ssh(self,computer,script):
        from .ssh_access import connect,execute
        with connect(computer,self.data) as client:return execute(client,script)
    def reconnect_remote(self,c):
        return self.ssh(c,"import os,subprocess\nos.environ['XDG_RUNTIME_DIR']=f'/run/user/{os.getuid()}'\nos.environ['DBUS_SESSION_BUS_ADDRESS']=f'unix:path={os.environ[\"XDG_RUNTIME_DIR\"]}/bus'\nsubprocess.run(['systemctl','--user','restart','synergy-dualboot.service'],check=True)\nprint('Client restarted.')\n")
    def local_fingerprint(self):
        import ssl
        cfg=config(self.custom/'core.conf')
        if not cfg.has_section('security'):cfg=config(self.original/'synergy-core.conf')
        cert=pathlib.Path(cfg.get('security','certificate').strip('"'))
        match=re.search(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----',cert.read_text(),re.S)
        if not match:raise ValueError('The desktop certificate could not be read.')
        return hashlib.sha256(ssl.PEM_cert_to_DER_cert(match.group())).hexdigest()
    def publish_identity(self):
        fingerprint=self.local_fingerprint();shared=self.shared()
        identities={}
        if shared and shared.is_dir():
            path=shared/'server-identities.json'
            if path.exists():identities=json.loads(path.read_text()).get('servers',{})
            identities['Windows' if WINDOWS else 'Linux']=fingerprint
            if any(not re.fullmatch(r'[0-9a-f]{64}',v) for v in identities.values()):raise ValueError('The shared server fingerprint file contains an invalid identity.')
            atomic(path,json.dumps({'schema':1,'servers':identities},indent=2))
        return list(dict.fromkeys([fingerprint,*identities.values()]))
    def configure_remote(self,c):
        from .remote_setup import remote_script
        fingerprints=self.publish_identity()
        addresses=self.settings.get('server_addresses',[])
        if not addresses:
            addresses=[a for a in socket.gethostbyname_ex(socket.gethostname())[2] if not a.startswith('127.')]
        if not addresses:raise ValueError('Add the desktop’s LAN/Tailscale addresses in Settings first.')
        return self.ssh(c,remote_script(c.screen,addresses,fingerprints))
    def export_profile(self,desk,path):atomic(path,json.dumps(desk.to_dict(),indent=2))
    def setup_local(self,role,screen,server_addresses,desk=None):
        from .setup import setup
        return setup(self,role,screen,server_addresses,desk)
