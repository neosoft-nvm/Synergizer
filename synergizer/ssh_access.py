"""GUI-paired SSH access. Passwords are transient; each OS owns its key."""
import base64,hashlib,io,json,os,pathlib,socket
import paramiko

class UnknownHost(RuntimeError):pass

def inspect_host(address,known_file):
    with socket.create_connection((address,22),timeout=6) as sock:
        transport=paramiko.Transport(sock)
        try:transport.start_client(timeout=6);key=transport.get_remote_server_key()
        finally:transport.close()
    fingerprint='SHA256:'+base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip('=')
    known=paramiko.HostKeys()
    for p in [pathlib.Path.home()/'.ssh/known_hosts',known_file]:
        if p.exists():
            loaded=paramiko.HostKeys(str(p))
            for host,keys in loaded.items():
                for kind,k in keys.items():known.add(host,kind,k)
    existing=known.lookup(address)
    trusted=existing is not None and key.get_name() in existing and existing[key.get_name()]==key
    return {'address':address,'type':key.get_name(),'key':key.get_base64(),'fingerprint':fingerprint,'trusted':trusted,'changed':bool(existing) and not trusted}

def trust_host(info,known_file):
    keys=paramiko.HostKeys()
    if known_file.exists():keys.load(str(known_file))
    key=paramiko.PKey.from_type_string(info['type'],base64.b64decode(info['key']))
    keys.add(info['address'],info['type'],key);keys.save(str(known_file))
    if os.name!='nt':known_file.chmod(0o600)

def protect_windows(data,encrypt):
    import ctypes
    from ctypes import wintypes
    class BLOB(ctypes.Structure):_fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_ubyte))]
    buffer=ctypes.create_string_buffer(data);source=BLOB(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));dest=BLOB()
    crypt=ctypes.windll.crypt32
    if encrypt:ok=crypt.CryptProtectData(ctypes.byref(source),None,None,None,None,1,ctypes.byref(dest))
    else:ok=crypt.CryptUnprotectData(ctypes.byref(source),None,None,None,None,1,ctypes.byref(dest))
    if not ok:raise RuntimeError('Windows could not protect the pairing key for your user account.')
    try:return ctypes.string_at(dest.pbData,dest.cbData)
    finally:ctypes.windll.kernel32.LocalFree(dest.pbData)

def pairing_key(data_dir,create=False):
    path=data_dir/('pairing-key.dpapi' if os.name=='nt' else 'pairing-key.pem')
    if not path.exists():
        if not create:return None
        key=paramiko.RSAKey.generate(3072);buf=io.StringIO();key.write_private_key(buf);data=buf.getvalue().encode()
        path.write_bytes(protect_windows(data,True) if os.name=='nt' else data)
        if os.name!='nt':path.chmod(0o600)
        return key
    data=path.read_bytes()
    if os.name=='nt':data=protect_windows(data,False)
    return paramiko.RSAKey.from_private_key(io.StringIO(data.decode()))

def connect(c,data_dir,password=None):
    if not c.addresses or not c.username:raise RuntimeError('Enter this computer’s address and SSH username in Edit first.')
    client=paramiko.SSHClient()
    system=pathlib.Path.home()/'.ssh/known_hosts'
    if system.exists():client.load_host_keys(str(system))
    if (data_dir/'known_hosts').exists():
        pinned=paramiko.HostKeys(str(data_dir/'known_hosts'))
        for host,keys in pinned.items():
            for kind,key in keys.items():client.get_host_keys().add(host,kind,key)
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:client.connect(c.addresses[0],username=c.username,password=password or None,pkey=pairing_key(data_dir),timeout=6,auth_timeout=10,banner_timeout=8,allow_agent=True,look_for_keys=True)
    except paramiko.AuthenticationException:
        client.close();raise RuntimeError('SSH sign-in failed. Check the username, then use Set up connection to authorize this app with the laptop’s password or an existing SSH key.')
    except Exception:
        client.close();raise
    return client

def execute(client,script):
    stdin,stdout,stderr=client.exec_command('python3 -',timeout=45)
    stdin.write(script);stdin.flush();stdin.channel.shutdown_write()
    output=stdout.read().decode(errors='replace');errors=stderr.read().decode(errors='replace');code=stdout.channel.recv_exit_status()
    if code:raise RuntimeError((errors or output or f'Remote setup failed ({code})')[-2500:])
    return output.strip()

def authorize(c,data_dir,password=None):
    key=pairing_key(data_dir,create=True)
    with connect(c,data_dir,password) as client:
        public=key.get_name()+' '+key.get_base64()+' synergizer'
        script="import pathlib,os\nh=pathlib.Path.home()/'.ssh';h.mkdir(mode=0o700,exist_ok=True);h.chmod(0o700)\np=h/'authorized_keys'\nold=p.read_text() if p.exists() else ''\nline="+repr(public)+"\nif line not in old:p.write_text(old.rstrip()+'\\n'+line+'\\n')\np.chmod(0o600)\nprint('Synergizer pairing key authorized.')\n"
        return execute(client,script)
