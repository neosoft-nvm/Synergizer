import pathlib,tempfile,unittest,json
from unittest.mock import patch
from synergizer.backend import Backend
from synergizer.model import Desk,Computer
class Transactions(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name);self.b=Backend(self.root/'data');self.b.custom=self.root/'custom';self.b.custom.mkdir();self.b.layout=self.b.custom/'layout.conf';self.b.core=self.root/'engine';self.b.core.touch();(self.b.custom/'core.conf').write_text('[core]\ncomputerName=desktop\ncoreMode=2\n');self.d=Desk([Computer('desktop','Desktop',primary=True)]);self.b.layout.write_text('old-layout');self.b.restart=lambda:'ok'
 def tearDown(self):self.temp.cleanup()
 def test_apply_and_backup(self):
  backup=self.b.apply(self.d);self.assertEqual(self.b.layout.read_text(),self.d.compile());self.assertEqual((backup/'layout.conf').read_text(),'old-layout')
 def test_failed_restart_rolls_back(self):
  self.b.restart=lambda:(_ for _ in ()).throw(RuntimeError('failure'))
  with self.assertRaises(RuntimeError):self.b.apply(self.d)
  self.assertEqual(self.b.layout.read_text(),'old-layout');self.assertFalse(self.b.profile.exists())
 def test_shared_apply(self):
  shared=self.root/'shared';shared.mkdir();self.b.settings['shared_folder']=str(shared);self.b.apply(self.d);self.assertEqual((shared/'layout.conf').read_text(),self.b.layout.read_text());self.assertEqual(json.loads((shared/'desk.json').read_text())['revision'],self.d.revision)
 def test_unavailable_shared_drive(self):
  self.b.settings['shared_folder']=str(self.root/'unmounted')
  with self.assertRaises(RuntimeError):self.b.apply(self.d)
  self.assertEqual(self.b.layout.read_text(),'old-layout')
 def test_client_cannot_apply(self):
  (self.b.custom/'core.conf').write_text('[core]\ncomputerName=desktop\ncoreMode=1\n')
  with self.assertRaises(RuntimeError):self.b.apply(self.d)
 def test_primary_identity_is_preserved(self):
  self.d.computers[0].screen='other'
  with self.assertRaises(RuntimeError):self.b.apply(self.d)
 def test_shared_sync(self):
  shared=self.root/'shared';shared.mkdir();self.b.settings['shared_folder']=str(shared);(shared/'desk.json').write_text(json.dumps(self.d.to_dict()));self.b.sync();self.assertEqual(self.b.layout.read_text(),self.d.compile())
 def test_rollback_reverts_shared_revision(self):
  shared=self.root/'shared';shared.mkdir();self.b.settings['shared_folder']=str(shared);(shared/'desk.json').write_text('old-profile');(shared/'layout.conf').write_text('old-shared-layout');self.b.restart=lambda:(_ for _ in ()).throw(RuntimeError('failure'))
  with self.assertRaises(RuntimeError):self.b.apply(self.d)
  self.assertEqual((shared/'desk.json').read_text(),'old-profile');self.assertEqual((shared/'layout.conf').read_text(),'old-shared-layout')

 def test_dual_boot_public_identities(self):
  shared=self.root/'shared';shared.mkdir();self.b.settings['shared_folder']=str(shared)
  (shared/'server-identities.json').write_text(json.dumps({'schema':1,'servers':{'OtherOS':'b'*64}}))
  self.b.local_fingerprint=lambda:'a'*64
  self.assertEqual(set(self.b.publish_identity()),{'a'*64,'b'*64})
  self.assertNotIn('PRIVATE KEY',(shared/'server-identities.json').read_text())
 def test_invalid_shared_identity_refused(self):
  shared=self.root/'shared';shared.mkdir();self.b.settings['shared_folder']=str(shared)
  (shared/'server-identities.json').write_text(json.dumps({'schema':1,'servers':{'OtherOS':'invalid'}}))
  self.b.local_fingerprint=lambda:'a'*64
  with self.assertRaises(ValueError):self.b.publish_identity()
