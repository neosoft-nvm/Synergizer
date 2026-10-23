"""Exercise the packaged executable, including Qt resources, without personal data."""
import os,pathlib,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
exe=root/'dist/Synergizer'/('Synergizer.exe' if os.name=='nt' else 'Synergizer')
licenses=root/'dist/Synergizer/THIRD-PARTY-LICENSES'
assert (licenses/'Qt/LGPL-3.0-only.txt').exists(),'Qt license notice is missing'
with tempfile.TemporaryDirectory() as t:
 env=dict(os.environ,QT_QPA_PLATFORM='offscreen');image=pathlib.Path(t)/'smoke.png'
 subprocess.run([str(exe),'--theme','dark','--data-dir',str(pathlib.Path(t)/'data'),'--screenshot',str(image)],check=True,env=env,timeout=45)
 assert image.stat().st_size>15000,'Packaged UI did not render'
 print('Packaged application rendered successfully:',image.stat().st_size,'bytes')
