import os,pathlib,tempfile,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from synergizer.ui import Window,ScreenItem
from synergizer.backend import Backend
from synergizer.model import Desk,Computer
app=QApplication.instance() or QApplication([])
class UITests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.b=Backend(pathlib.Path(self.tmp.name)/'data');self.b.load=lambda:Desk([Computer('laptop','Laptop',0,0),Computer('desktop','Desktop',1,0,True)]);self.b.status=lambda d:{'desktop':'Running','laptop':'Connected'};self.w=Window(self.b,'dark');self.w.timer.stop()
 def tearDown(self):
  self.w.dirty=False;self.w.close();self.w.deleteLater();app.processEvents();self.tmp.cleanup()
 def test_real_canvas(self):self.assertEqual(len([i for i in self.w.scene.items() if isinstance(i,ScreenItem)]),2)
 def test_primary_cannot_be_removed(self):self.w.select('desktop');self.assertFalse(self.w.remove_btn.isEnabled())
 def test_secondary_can_be_removed(self):self.w.select('laptop');self.assertTrue(self.w.remove_btn.isEnabled())
 def test_unsaved_undo(self):self.w.desk.computers[0].x=-1;self.w.mark_dirty();self.w.undo();self.assertEqual(self.w.desk.computers[0].x,0);self.assertFalse(self.w.dirty)
 def test_navigation_and_themes(self):
  for i in range(5):self.w.go(i);self.assertEqual(self.w.pages.currentIndex(),i)
  self.w.apply_theme('light');self.w.apply_theme('dark')
