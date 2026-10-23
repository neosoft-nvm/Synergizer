import argparse,os,pathlib,sys

def main():
    a=argparse.ArgumentParser(description='Synergizer — your desk, seamlessly connected')
    a.add_argument('--install',action='store_true');a.add_argument('--sync',action='store_true');a.add_argument('--theme',choices=['system','light','dark']);a.add_argument('--screenshot');a.add_argument('--data-dir');a.add_argument('--supervise',action='store_true');a.add_argument('--session-start',action='store_true')
    args=a.parse_args()
    if args.install:
        from .install import install_user
        install_user();return
    if args.sync:
        from .backend import Backend
        try:Backend(args.data_dir).sync()
        except Exception as e:print('Keeping last working desk:',e,flush=True)
        return
    if args.supervise or args.session_start:
        from .backend import Backend,config,run,WINDOWS
        b=Backend(args.data_dir)
        try:b.sync()
        except Exception as e:print('Shared desk unavailable; keeping last working layout:',e,flush=True)
        if args.session_start:
            if not WINDOWS:run(['systemctl','--user','import-environment',*[k for k in ('DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','XDG_SESSION_TYPE') if k in os.environ]])
            b.restart();return
        c=config(b.custom/'core.conf');role='server' if c.get('core','coreMode')=='2' else 'client'
        from .supervisor import supervise
        supervise(b.core,b.custom/'core.conf',role,c.getint('core','port',fallback=24800));return
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from PySide6.QtNetwork import QLocalServer,QLocalSocket
    app=QApplication(sys.argv[:1]);app.setApplicationName('Synergizer');app.setOrganizationName('Synergizer');app.setStyle('Fusion')
    from .backend import Backend
    from .ui import Window
    b=Backend(args.data_dir)
    server=None
    if not args.screenshot:
        import hashlib
        key='Synergizer-'+hashlib.sha256(str(b.data).encode()).hexdigest()[:16]
        socket=QLocalSocket();socket.connectToServer(key)
        if socket.waitForConnected(350):socket.write(b'open');socket.flush();socket.waitForBytesWritten(350);return
        QLocalServer.removeServer(key);server=QLocalServer();server.listen(key)
    window=Window(b,args.theme);window.show()
    if server:
        def activate():
            connection=server.nextPendingConnection()
            if connection:connection.close();connection.deleteLater()
            window.show_raise()
        server.newConnection.connect(activate)
    if args.screenshot:
        def capture():
            path=pathlib.Path(args.screenshot);path.parent.mkdir(parents=True,exist_ok=True)
            window.grab().save(str(path));app.quit()
        QTimer.singleShot(1600,capture)
    result=app.exec()
    # A pending local-status query must finish before QRunnable/Qt teardown.
    from PySide6.QtCore import QThreadPool
    QThreadPool.globalInstance().waitForDone(25000)
    return result
