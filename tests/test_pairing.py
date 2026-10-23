import os,pathlib,tempfile,unittest
from synergizer.ssh_access import pairing_key,trust_host
from synergizer.remote_setup import remote_script
class PairingTests(unittest.TestCase):
 def test_pairing_key_persists(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);first=pairing_key(root,True);second=pairing_key(root)
   self.assertEqual(first.get_base64(),second.get_base64())
   if os.name!='nt':self.assertEqual((root/'pairing-key.pem').stat().st_mode & 0o777,0o600)
 def test_host_key_pin(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);key=pairing_key(root,True);trust_host({'address':'example.test','type':key.get_name(),'key':key.get_base64()},root/'known_hosts');self.assertIn(key.get_base64(),(root/'known_hosts').read_text())
 def test_generated_remote_setup_is_valid_python(self):
  script=remote_script('work-laptop',['192.0.2.20'],'a'*64);compile(script,'remote-setup','exec')
  self.assertIn('Backup:',script)
