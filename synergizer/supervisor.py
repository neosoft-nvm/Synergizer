"""Sharing process supervision. No Qt imports, so clients need only Python."""
import os, pathlib, signal, socket, subprocess, sys, time

def has_connection(pid,port):
    if os.name=='nt':
        try:
            flags=subprocess.CREATE_NO_WINDOW
            result=subprocess.run(['netstat','-ano','-p','tcp'],capture_output=True,text=True,creationflags=flags,timeout=8)
            return any(str(pid)==v[-1] and v[3]=='ESTABLISHED' and v[2].endswith(':'+str(port)) for line in result.stdout.splitlines() if len(v:=line.split())>=5)
        except (OSError,subprocess.TimeoutExpired):return True
    try:
        inodes={os.readlink(p)[8:-1] for p in pathlib.Path(f'/proc/{pid}/fd').iterdir() if os.readlink(p).startswith('socket:[')}
        for family in ('tcp','tcp6'):
            for line in pathlib.Path(f'/proc/{pid}/net/{family}').read_text().splitlines()[1:]:
                v=line.split()
                if len(v)>9 and v[3]=='01' and int(v[2].split(':')[-1],16)==port and v[9] in inodes:return True
        return False
    except OSError:return True

def supervise(core,settings,role,port=24800):
    child=None;stopping=False
    def stop(*_):
        nonlocal stopping
        stopping=True
        if child and child.poll() is None:child.terminate()
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    while not stopping:
        kwargs={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
        log=None
        if os.name=='nt':
            path=pathlib.Path(settings).parent/'sharing.log'
            if path.exists() and path.stat().st_size>5_000_000:path.replace(path.with_suffix('.previous.log'))
            log=path.open('a',encoding='utf-8')
            kwargs.update(stdout=log,stderr=subprocess.STDOUT)
        child=subprocess.Popen([str(core),role,'--settings',str(settings)],**kwargs)
        last_healthy=time.monotonic()
        while child.poll() is None and not stopping:
            time.sleep(3)
            if role=='client':
                if has_connection(child.pid,port):last_healthy=time.monotonic()
                elif time.monotonic()-last_healthy>90:
                    print('Synergizer: restarting disconnected client after 90 seconds.',flush=True);child.terminate()
                    try:child.wait(10)
                    except subprocess.TimeoutExpired:child.kill()
        if child.poll() is None:
            child.terminate()
            try:child.wait(10)
            except subprocess.TimeoutExpired:child.kill()
        if log:log.close()
        if not stopping:time.sleep(5)
