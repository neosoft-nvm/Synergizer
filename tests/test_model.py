import copy,unittest
from synergizer.model import Computer,Desk,parse_layout
class LayoutTests(unittest.TestCase):
 def setUp(self):self.d=Desk([Computer('left','Left',0,0),Computer('middle','Middle',1,0),Computer('desktop','Desktop',2,0,True)])
 def test_roundtrip(self):
  self.d.computers[0].options=['alt = alt','halfDuplexCapsLock = false'];out=self.d.compile();d=parse_layout(out,'desktop');self.assertEqual(d.compile(),out)
 def test_vertical_and_branch(self):
  self.d.computers.append(Computer('above','Above',1,-1));self.assertIn('up = above',self.d.compile());self.assertIn('down = middle',self.d.compile())
 def test_overlap(self):
  self.d.computers[0].x=1
  with self.assertRaisesRegex(ValueError,'same position'):self.d.compile()
 def test_disconnected(self):
  self.d.computers[0].x=-2
  with self.assertRaisesRegex(ValueError,'Bring'):self.d.compile()
 def test_duplicates(self):
  self.d.computers[0].screen='desktop'
  with self.assertRaises(ValueError):self.d.compile()
 def test_no_primary(self):
  self.d.computers[2].primary=False
  with self.assertRaises(ValueError):self.d.compile()
 def test_invalid_name(self):
  self.d.computers[0].screen='bad\nend'
  with self.assertRaises(ValueError):self.d.compile()
 def test_option_injection(self):
  self.d.options=['heartbeat = 5000\nend']
  with self.assertRaises(ValueError):self.d.compile()
 def test_large_coordinate(self):
  self.d.computers[0].x=100000000
  with self.assertRaises(ValueError):self.d.compile()
 def test_partial_edge_refused(self):
  with self.assertRaisesRegex(ValueError,'partial-edge'):parse_layout(self.d.compile().replace('right = middle','right(0,50) = middle'))
 def test_wrap_refused(self):
  with self.assertRaises(ValueError):parse_layout(self.d.compile().replace('left = middle','right = middle'))
 def test_unknown_section_refused(self):
  with self.assertRaises(ValueError):parse_layout(self.d.compile()+'section: aliases\n desktop:\n  other\nend')
 def test_json_profile(self):self.assertEqual(Desk.from_dict(self.d.to_dict()).compile(),self.d.compile())
