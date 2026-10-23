from __future__ import annotations
import copy,json,os,pathlib,sys,traceback
from PySide6.QtCore import Qt,QRectF,QPointF,QTimer,Signal,QObject,QRunnable,QThreadPool,QSettings
from PySide6.QtGui import QColor,QFont,QPainter,QPen,QBrush,QPainterPath,QIcon,QDesktopServices,QAction,QKeySequence
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QFrame,QStackedWidget,QGraphicsView,QGraphicsScene,QGraphicsObject,QGraphicsItem,QGraphicsDropShadowEffect,QLineEdit,QFormLayout,QDialog,QDialogButtonBox,QComboBox,QMessageBox,QFileDialog,QPlainTextEdit,QCheckBox,QScrollArea,QListWidget,QListWidgetItem,QSystemTrayIcon,QMenu,QInputDialog,QSizePolicy)
from .model import Computer,Desk,SAFE_NAME
from .backend import Backend,WINDOWS
from . import __version__

DARK={'bg':'#0d141b','panel':'#131e27','canvas':'#0b1218','card':'#172630','line':'#293c47','text':'#eff6f6','muted':'#91a7b3','accent':'#78ecc1','accent_text':'#09251e','hover':'#20333e','danger':'#fb9c98','dot':'#1d2d37'}
LIGHT={'bg':'#f3f6f7','panel':'#ffffff','canvas':'#eaf0f2','card':'#ffffff','line':'#d5e1e5','text':'#172e39','muted':'#627c89','accent':'#147d68','accent_text':'#ffffff','hover':'#e5f2ed','danger':'#b9363f','dot':'#ccdce0'}

def asset(name):return pathlib.Path(__file__).parent/'assets'/name

def label(text,kind=''):
    w=QLabel(text);w.setWordWrap(kind in ('muted','notice','dialogTitle'))
    if kind:w.setObjectName(kind)
    return w

def button(text,callback=None,kind=''):
    b=QPushButton(text);b.setCursor(Qt.CursorShape.PointingHandCursor)
    if kind:b.setObjectName(kind)
    if callback:b.clicked.connect(callback)
    return b

def card():
    w=QFrame();w.setObjectName('panel');return w

class Signals(QObject):
    done=Signal(object);failed=Signal(str)
class Job(QRunnable):
    def __init__(self,fn):super().__init__();self.fn=fn;self.signals=Signals()
    def run(self):
        try:self.signals.done.emit(self.fn())
        except Exception as e:self.signals.failed.emit(str(e))

class ScreenItem(QGraphicsObject):
    def __init__(self,computer,window):
        super().__init__();self.c=computer;self.window=window
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable|QGraphicsItem.GraphicsItemFlag.ItemIsSelectable|QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setCursor(Qt.CursorShape.OpenHandCursor);self.setPos(computer.x*290,computer.y*210)
        self.setToolTip('Drag to move. Click to see computer details.')
    def boundingRect(self):return QRectF(-6,-6,272,176)
    def paint(self,p,option,widget=None):
        t=self.window.colors;c=self.c;selected=self.window.selected==c.screen
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(t['accent'] if selected else t['line']),2 if selected else 1));p.setBrush(QColor(t['card']));p.drawRoundedRect(QRectF(0,0,260,164),16,16)
        p.setPen(QPen(QColor(t['accent'] if c.primary else t['muted']),2))
        p.setBrush(QColor(t['canvas']));p.drawRoundedRect(QRectF(19,20,48,32),5,5);p.drawLine(43,53,43,61);p.drawLine(31,62,55,62)
        p.setPen(QColor(t['muted']));p.setFont(QFont(self.window.font().family(),9))
        p.drawText(QRectF(84,19,158,18),Qt.AlignmentFlag.AlignLeft,'KEYBOARD & MOUSE' if c.primary else 'CONNECTED COMPUTER')
        p.setPen(QColor(t['text']));p.setFont(QFont(self.window.font().family(),12,QFont.Weight.DemiBold))
        fm=p.fontMetrics();p.drawText(QRectF(19,79,223,24),Qt.AlignmentFlag.AlignLeft,fm.elidedText(c.label,Qt.TextElideMode.ElideRight,220))
        p.setFont(QFont(self.window.font().family(),9));p.setPen(QColor(t['muted']));p.drawText(QRectF(19,107,220,20),Qt.AlignmentFlag.AlignLeft,c.platform)
        status=self.window.statuses.get(c.screen,'Checking…')
        healthy=status in ('Running','Connected');color=t['accent'] if healthy else '#b8a16c'
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(color));p.drawEllipse(QPointF(23,143),3,3)
        p.setPen(QColor(t['muted']));p.setFont(QFont(self.window.font().family(),8));p.drawText(QRectF(35,134,200,18),Qt.AlignmentFlag.AlignLeft,status)
    def mousePressEvent(self,event):
        self.window.select(self.c.screen);self.setCursor(Qt.CursorShape.ClosedHandCursor);super().mousePressEvent(event)
    def mouseReleaseEvent(self,event):
        super().mouseReleaseEvent(event);self.setCursor(Qt.CursorShape.OpenHandCursor)
        x=max(-50,min(50,round(self.pos().x()/290)));y=max(-50,min(50,round(self.pos().y()/210)));self.setPos(x*290,y*210)
        if (x,y)!=(self.c.x,self.c.y):
            self.c.x=x;self.c.y=y;self.window.mark_dirty();QTimer.singleShot(0,self.window.render_desk)

class DeskScene(QGraphicsScene):
    def __init__(self,window):super().__init__();self.window=window
    def drawBackground(self,p,rect):
        t=self.window.colors;p.fillRect(rect,QColor(t['canvas']));p.setPen(QPen(QColor(t['dot']),1))
        for x in range(int(rect.left())//24*24,int(rect.right())+24,24):
            for y in range(int(rect.top())//24*24,int(rect.bottom())+24,24):p.drawPoint(x,y)
    def drawForeground(self,p,rect):pass

class DeskView(QGraphicsView):
    def __init__(self,scene):
        super().__init__(scene);self.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.TextAntialiasing);self.setFrameShape(QFrame.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag);self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse);self.setMinimumHeight(350)
    def wheelEvent(self,event):
        factor=1.12 if event.angleDelta().y()>0 else 1/1.12
        if .35<self.transform().m11()*factor<2.5:self.scale(factor,factor)

class ComputerDialog(QDialog):
    def __init__(self,parent,computer=None,found=()):
        super().__init__(parent);self.setWindowTitle('Edit computer' if computer else 'Add a computer');self.resize(490,420);self.original=computer
        root=QVBoxLayout(self);root.setContentsMargins(28,24,28,24);root.setSpacing(16)
        root.addWidget(label('Make room for another screen' if not computer else 'Computer details','dialogTitle'))
        root.addWidget(label('Synergy must already be installed and activated on this computer.','muted'))
        form=QFormLayout();form.setSpacing(12)
        self.name=QLineEdit(computer.label if computer else '');self.name.setPlaceholderText('e.g. Work laptop')
        self.address=QLineEdit(', '.join(computer.addresses) if computer else '');self.address.setPlaceholderText('IP address or host name')
        self.user=QLineEdit(computer.username if computer else '');self.user.setPlaceholderText('For guided setup and remote reconnect')
        self.screen=QLineEdit(computer.screen if computer else '');self.screen.setPlaceholderText('e.g. work-laptop');self.screen.setReadOnly(bool(computer))
        self.platform=QComboBox();self.platform.addItems(['Linux','Windows','Windows + Linux']);self.platform.setCurrentText(computer.platform if computer else 'Linux')
        if found:
            choose=QComboBox();choose.addItem('Choose a discovered computer…',None)
            for d in found:choose.addItem(d['label']+'  ·  '+d['address'],d)
            def chosen(i):
                d=choose.itemData(i)
                if d:self.name.setText(d['label']);self.address.setText(d['address'])
            choose.currentIndexChanged.connect(chosen);form.addRow('Found on your network',choose)
        for title,field in [('Name',self.name),('Address',self.address),('SSH username',self.user),('Synergy screen name',self.screen),('Operating system',self.platform)]:form.addRow(title,field)
        root.addLayout(form)
        self.error=label('','error');root.addWidget(self.error)
        box=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);box.accepted.connect(self.accept_checked);box.rejected.connect(self.reject);root.addWidget(box)
    def accept_checked(self):
        name=self.name.text().strip();screen=self.screen.text().strip() or __import__('re').sub('[^a-z0-9_.-]+','-',name.lower()).strip('-')
        if not name or not SAFE_NAME.fullmatch(screen):self.error.setText('Enter a name and a screen name using letters, numbers, periods or hyphens.');return
        self.value=Computer(screen,name,addresses=[v.strip() for v in self.address.text().split(',') if v.strip()],username=self.user.text().strip(),platform=self.platform.currentText())
        self.accept()

class Window(QMainWindow):
    def __init__(self,backend=None,theme=None):
        super().__init__();self.backend=backend or Backend();self.statuses={};self.selected=None;self.dirty=False;self.jobs=[];self.status_pending=False
        try:self.desk=self.backend.load();self.load_error=''
        except Exception as e:self.desk=Desk();self.load_error=str(e)
        self.saved=copy.deepcopy(self.desk);self.forced_theme=theme
        self.setWindowTitle('Synergizer — Your desk, seamlessly connected');self.setWindowIcon(QIcon(str(asset('synergizer.svg'))));self.resize(1280,820);self.setMinimumSize(1060,700)
        self.apply_theme(theme or self.backend.settings.get('theme','system'))
        container=QWidget();self.setCentralWidget(container);outer=QHBoxLayout(container);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        self.sidebar=QFrame();self.sidebar.setObjectName('sidebar');self.sidebar.setFixedWidth(210);side=QVBoxLayout(self.sidebar);side.setContentsMargins(22,28,22,22);side.setSpacing(8)
        brand=QHBoxLayout();logo=QLabel();logo.setStyleSheet('background:transparent;');logo.setPixmap(QIcon(str(asset('synergizer.svg'))).pixmap(38,38));brand.addWidget(logo);brand.addWidget(label('Synergizer','brand'));side.addLayout(brand)
        side.addSpacing(14);side.addWidget(label('YOUR WORKSPACE','eyebrow'));side.addSpacing(8)
        self.pages=QStackedWidget();self.nav=[]
        for i,(name,glyph) in enumerate([('My desk','▦'),('Computers','▤'),('Recovery','↻'),('Backups','◷'),('Settings','⚙')]):
            b=button(glyph+'   '+name,lambda checked=False,n=i:self.go(n),'nav');b.setCheckable(True);side.addWidget(b);self.nav.append(b)
        side.addStretch()
        foot=card();foot.setMinimumHeight(150);fl=QVBoxLayout(foot);fl.setContentsMargins(14,14,14,14);foot_title=label('One desk. Two operating systems.','smallTitle');foot_title.setWordWrap(True);fl.addWidget(foot_title);fl.addWidget(label('Your desktop stays in the same place when you switch.','muted'));side.addWidget(foot)
        side.addSpacing(12);version_label=label('SYNERGY 3 COMPANION  /  '+__version__,'eyebrow');version_label.setWordWrap(True);side.addWidget(version_label);outer.addWidget(self.sidebar)
        main=QWidget();ml=QVBoxLayout(main);ml.setContentsMargins(28,24,28,20);ml.setSpacing(16)
        top=QHBoxLayout();self.page_title=label('My desk','pageTitle');top.addWidget(self.page_title);top.addStretch()
        self.sync_badge=label('●  '+('Shared desk' if self.backend.shared() else 'Local desk'),'badge');top.addWidget(self.sync_badge);top.addSpacing(12);top.addWidget(button('Find computers',self.find_computers,'secondary'));ml.addLayout(top)
        self.notice=label('','notice');self.notice.hide();ml.addWidget(self.notice)
        self.pages.addWidget(self.desk_page());self.pages.addWidget(self.computers_page());self.pages.addWidget(self.recovery_page());self.pages.addWidget(self.backups_page());self.pages.addWidget(self.settings_page())
        ml.addWidget(self.pages,1)
        footer=QHBoxLayout();self.footer=label('Your working configuration is preserved until you apply changes.','muted');footer.addWidget(self.footer,1);credit=label('Made for the way you work.','muted');credit.setWordWrap(False);footer.addWidget(credit);ml.addLayout(footer)
        outer.addWidget(main,1);self.go(0);self.render_desk();self.refresh_computers();self.refresh_backups()
        self.tray=QSystemTrayIcon(self.windowIcon(),self);self.tray.setToolTip('Synergizer — Open your desk');menu=QMenu();menu.addAction('Open Synergizer',self.show_raise);menu.addAction('Reconnect sharing',self.reconnect);menu.addSeparator();menu.addAction('Quit Synergizer',self.close);self.tray.setContextMenu(menu);self.tray.activated.connect(lambda r:self.show_raise() if r==QSystemTrayIcon.ActivationReason.Trigger else None)
        if QSystemTrayIcon.isSystemTrayAvailable():self.tray.show()
        act=QAction(self);act.setShortcut(QKeySequence.StandardKey.Save);act.triggered.connect(self.apply_changes);self.addAction(act)
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh_status);self.timer.start(12000);QTimer.singleShot(200,self.refresh_status)
        if self.load_error:self.message('Import needs attention: '+self.load_error)
        elif not self.desk.computers:self.message('Welcome! Install Synergy 3, then use Settings → Import existing desk or Set up sharing.')
    def apply_theme(self,mode):
        dark=(mode=='dark') or (mode=='system' and QApplication.styleHints().colorScheme()==Qt.ColorScheme.Dark)
        self.colors=DARK if dark else LIGHT;t=self.colors
        self.setStyleSheet(f'''
QWidget {{background:{t['bg']};color:{t['text']};font-family:"Inter","Segoe UI","Noto Sans",sans-serif;font-size:13px;}}
QFrame#sidebar {{background:{t['panel']};border-right:1px solid {t['line']};}}
QFrame#panel {{background:{t['panel']};border:1px solid {t['line']};border-radius:14px;}}
QFrame#panel QLabel {{background:transparent;}}
QLabel#brand {{font-size:19px;font-weight:700;background:transparent;}}
QLabel#pageTitle {{font-size:21px;font-weight:650;}}
QLabel#hero {{font-size:28px;font-weight:700;}}
QLabel#dialogTitle {{font-size:21px;font-weight:650;}}
QLabel#smallTitle {{font-weight:650;font-size:13px;}}
QLabel#muted {{color:{t['muted']};font-size:12px;}}
QLabel#eyebrow {{color:{t['muted']};font-size:9px;font-weight:600;letter-spacing:1px;background:transparent;}}
QLabel#badge {{color:{t['accent']};background:{t['panel']};border:1px solid {t['line']};border-radius:12px;padding:7px 12px;font-size:11px;}}
QLabel#notice {{background:{t['hover']};color:{t['text']};border:1px solid {t['line']};border-radius:10px;padding:12px;}}
QLabel#error {{color:{t['danger']};}}
QPushButton {{background:{t['panel']};border:1px solid {t['line']};border-radius:9px;padding:10px 15px;font-weight:550;}}
QPushButton:hover {{background:{t['hover']};border-color:{t['muted']};}}
QPushButton:disabled {{color:{t['muted']};background:{t['bg']};}}
QPushButton#primary {{background:{t['accent']};color:{t['accent_text']};border-color:{t['accent']};}}
QPushButton#primary:disabled {{background:{t['line']};color:{t['muted']};border-color:{t['line']};}}
QPushButton#danger {{color:{t['danger']};}}
QPushButton#nav {{text-align:left;border:0;background:transparent;font-size:12px;padding:13px 10px;}}
QPushButton#nav:checked {{background:{t['hover']};color:{t['accent']};}}
QPushButton#nav:hover {{background:{t['hover']};}}
QLineEdit,QComboBox,QPlainTextEdit,QListWidget {{background:{t['panel']};border:1px solid {t['line']};border-radius:8px;padding:9px;selection-background-color:{t['accent']};selection-color:{t['accent_text']};}}
QLineEdit:focus,QComboBox:focus {{border-color:{t['accent']};}}
QComboBox::drop-down {{border:0;width:24px;}}
QScrollArea {{border:0;background:transparent;}}
QScrollBar:vertical {{background:{t['bg']};width:9px;}} QScrollBar::handle:vertical {{background:{t['line']};border-radius:4px;min-height:25px;}}
QToolTip {{background:{t['panel']};color:{t['text']};border:1px solid {t['line']};padding:6px;}}
QMenu {{background:{t['panel']};border:1px solid {t['line']};padding:6px;}}
QMenu::item {{padding:9px 24px;}} QMenu::item:selected {{background:{t['hover']};}}
QDialogButtonBox QPushButton {{min-width:75px;}}
''')
    def show_raise(self):self.showNormal();self.raise_();self.activateWindow()
    def work(self,fn,done=None):
        job=Job(fn);self.jobs.append(job)
        def complete(value):
            if job in self.jobs:self.jobs.remove(job)
            if done:done(value)
        def failed(text):
            if job in self.jobs:self.jobs.remove(job)
            self.status_pending=False
            if hasattr(self,'apply_btn'):self.apply_btn.setEnabled(self.dirty)
            self.message(text)
        job.signals.done.connect(complete);job.signals.failed.connect(failed);QThreadPool.globalInstance().start(job)
    def message(self,text):self.notice.setText(text);self.notice.show()
    def go(self,index):
        self.pages.setCurrentIndex(index)
        for i,b in enumerate(self.nav):b.setChecked(i==index)
        self.page_title.setText(['My desk','Computers','Connection & recovery','Backups','Settings'][index])
        if index==3:self.refresh_backups()
    def desk_page(self):
        w=QWidget();v=QVBoxLayout(w);v.setContentsMargins(0,0,0,0);v.setSpacing(16)
        heading=QHBoxLayout();words=QVBoxLayout();words.addWidget(label('A place for every screen.','hero'));words.addWidget(label('Arrange your computers the way they sit on your desk.','muted'));heading.addLayout(words,1);self.undo_btn=button('↶  Undo',self.undo);heading.addWidget(self.undo_btn);self.apply_btn=button('Apply changes',self.apply_changes,'primary');heading.addWidget(self.apply_btn);v.addLayout(heading)
        stats=QHBoxLayout();self.count_label=label('','smallTitle');self.health_label=label('Checking connections…','muted');self.health_label.setWordWrap(False);stats.addWidget(self.count_label);stats.addSpacing(22);stats.addWidget(self.health_label);stats.addStretch();encrypted=label('●  Encrypted Synergy connections','muted');encrypted.setWordWrap(False);stats.addWidget(encrypted);v.addLayout(stats)
        self.canvas_frame=card();cv=QVBoxLayout(self.canvas_frame);cv.setContentsMargins(1,1,1,1);cv.setSpacing(0)
        tools=QHBoxLayout();tools.setContentsMargins(16,12,16,12);tools.addWidget(label('DESK LAYOUT','eyebrow'));tools.addStretch();tools.addWidget(button('−',lambda:self.view.scale(.85,.85)));tools.addWidget(button('Fit desk',self.fit));tools.addWidget(button('+',lambda:self.view.scale(1.15,1.15)));cv.addLayout(tools)
        self.scene=DeskScene(self);self.view=DeskView(self.scene);cv.addWidget(self.view,1)
        hint=QHBoxLayout();hint.setContentsMargins(16,12,16,12);helptext=label('Drag to move  ·  Click for details  ·  Scroll to zoom','muted');helptext.setWordWrap(False);hint.addWidget(helptext);hint.addStretch();hint.addWidget(button('+ Add computer',self.add_computer));cv.addLayout(hint);v.addWidget(self.canvas_frame,1)
        self.details=card();dl=QHBoxLayout(self.details);dl.setContentsMargins(18,14,18,14);text=QVBoxLayout();self.detail_title=label('Select a computer','smallTitle');self.detail_sub=label('Windows and Linux share one desktop tile. Individual monitors are arranged in your operating system’s display settings.','muted');text.addWidget(self.detail_title);text.addWidget(self.detail_sub);dl.addLayout(text,1)
        self.edit_btn=button('Edit',self.edit_selected);self.remove_btn=button('Remove',self.remove_selected,'danger');dl.addWidget(self.edit_btn);dl.addWidget(self.remove_btn);v.addWidget(self.details)
        return w
    def computers_page(self):
        w=QWidget();v=QVBoxLayout(w);v.setContentsMargins(0,0,0,0);v.addWidget(label('Everyone at your desk.','hero'));v.addWidget(label('Friendly names on the outside. Stable Synergy identities underneath.','muted'))
        self.computer_list=QVBoxLayout();v.addLayout(self.computer_list);v.addStretch();v.addWidget(button('+ Add a computer',self.add_computer,'primary'));return w
    def recovery_page(self):
        w=QWidget();v=QVBoxLayout(w);v.setContentsMargins(0,0,0,0);v.setSpacing(16)
        v.addWidget(label('Get back to your flow.','hero'));v.addWidget(label('Check what is happening, reconnect sharing, or recover a known-good desk.','muted'))
        p=card();l=QVBoxLayout(p);l.setContentsMargins(24,24,24,24);l.setSpacing(14);l.addWidget(label('Keyboard and mouse sharing','smallTitle'));self.recovery_status=label('Checking…','muted');l.addWidget(self.recovery_status);l.addWidget(button('Reconnect this computer',self.reconnect,'primary'));l.addWidget(label('Receiving computers configured by Synergizer automatically retry when the desktop becomes available and recover stalled clients. Wi-Fi and the laptop itself must be awake.','muted'));v.addWidget(p)
        row=QHBoxLayout();row.addWidget(button('Refresh connection status',self.refresh_status));row.addWidget(button('Show sharing logs',self.show_logs));row.addWidget(button('Export diagnostics',self.export_diagnostics));v.addLayout(row)
        v.addWidget(label('Backups are created before every layout change. You can restore one from the Backups page.','muted'));v.addStretch();return w
    def backups_page(self):
        w=QWidget();v=QVBoxLayout(w);v.setContentsMargins(0,0,0,0);v.addWidget(label('Room to change your mind.','hero'));v.addWidget(label('Every applied layout gets a recovery point. Restore it without editing a configuration file.','muted'));self.backup_list=QListWidget();v.addWidget(self.backup_list,1)
        row=QHBoxLayout();row.addWidget(button('Create backup now',self.create_backup));row.addStretch();row.addWidget(button('Restore selected backup',self.restore_selected,'primary'));v.addLayout(row);return w
    def settings_page(self):
        w=QWidget();outer=QVBoxLayout(w);outer.setContentsMargins(0,0,0,0);scroll=QScrollArea();scroll.setWidgetResizable(True);inner=QWidget();v=QVBoxLayout(inner);v.setContentsMargins(0,0,8,0);v.setSpacing(18)
        v.addWidget(label('Make it yours.','hero'))
        appearance=card();form=QFormLayout(appearance);form.setContentsMargins(22,20,22,20);form.setSpacing(14);theme=QComboBox();theme.addItems(['System','Light','Dark']);theme.setCurrentText(self.backend.settings.get('theme','system').title());theme.currentTextChanged.connect(self.change_theme);form.addRow('Appearance',theme);v.addWidget(appearance)
        shared=card();sl=QVBoxLayout(shared);sl.setContentsMargins(22,20,22,20);sl.addWidget(label('Keep Windows and Linux in step','smallTitle'));sl.addWidget(label('Choose the same shared folder from both operating systems. It holds only your desk profile and layout. Passwords and private keys stay on each computer.','muted'));self.shared_field=QLineEdit(self.backend.settings.get('shared_folder',''));self.shared_field.setReadOnly(True);r=QHBoxLayout();r.addWidget(self.shared_field,1);r.addWidget(button('Choose folder',self.choose_shared));sl.addLayout(r);sl.addWidget(label('On Linux, mount your Windows data partition first. The last working layout is kept if the shared drive is unavailable.','muted'));v.addWidget(shared)
        net=card();nl=QFormLayout(net);nl.setContentsMargins(22,20,22,20);self.server_field=QLineEdit(', '.join(self.backend.settings.get('server_addresses',[])));self.server_field.setPlaceholderText('Desktop LAN address, optional Tailscale addresses');nl.addRow('Desktop addresses',self.server_field);nl.addRow('',button('Save desktop addresses',self.save_addresses));v.addWidget(net)
        setup=card();bl=QVBoxLayout(setup);bl.setContentsMargins(22,20,22,20);bl.setSpacing(12);bl.addWidget(label('Sharing setup','smallTitle'));bl.addWidget(label('Synergizer is a companion for Synergy 3. Install and activate Synergy separately on each computer.','muted'));bl.addWidget(button('Set up sharing on this computer',self.setup_local));bl.addWidget(button('Import existing desk',self.import_existing));r=QHBoxLayout();r.addWidget(button('Export desk profile',self.export_profile));r.addWidget(button('Import desk profile',self.import_profile));bl.addLayout(r);v.addWidget(setup)
        v.addWidget(label('Synergizer '+__version__+'  ·  An independent companion, not affiliated with Symless.','muted'));v.addStretch();scroll.setWidget(inner);outer.addWidget(scroll);return w
    def change_theme(self,text):
        self.backend.settings['theme']=text.lower();self.backend.save_settings();self.apply_theme(text.lower());self.render_desk()
    def choose_shared(self):
        initial=str(self.backend.shared() or (pathlib.Path(os.environ.get('PROGRAMDATA','C:/ProgramData'))/'Synergy-DualBoot' if WINDOWS else pathlib.Path('/mnt/windows/ProgramData/Synergy-DualBoot')))
        path=QFileDialog.getExistingDirectory(self,'Choose the shared Windows/Linux folder',initial)
        if not path:return
        p=pathlib.Path(path)
        if (p/'desk.json').exists() and self.confirm('Use the desk saved here?','This shared folder already contains a desk profile. Load it into the editor?'):
            try:self.desk=Desk.from_dict(json.loads((p/'desk.json').read_text()));self.mark_dirty();self.render_desk()
            except Exception as e:self.message(str(e));return
        self.backend.settings['shared_folder']=path;self.backend.save_settings();self.shared_field.setText(path);self.sync_badge.setText('●  Shared desk');self.work(self.backend.publish_identity,lambda _:None);self.message('Shared folder selected. Apply your desk to save it here. Select this same folder in the other OS too.')
    def save_addresses(self):
        self.backend.settings['server_addresses']=[a.strip() for a in self.server_field.text().split(',') if a.strip()];self.backend.save_settings();self.message('Desktop addresses saved for guided client setup.')
    def render_desk(self):
        self.scene.clear();active=[c for c in self.desk.computers if c.enabled];t=self.colors
        for c in active:
            for o in active:
                if (o.x,o.y) in ((c.x+1,c.y),(c.x,c.y+1)):
                    if o.x>c.x:a=QPointF(c.x*290+260,c.y*210+82);b=QPointF(o.x*290,o.y*210+82)
                    else:a=QPointF(c.x*290+130,c.y*210+164);b=QPointF(o.x*290+130,o.y*210)
                    path=QPainterPath(a);path.lineTo(b);self.scene.addPath(path,QPen(QColor(t['accent']),2,Qt.PenStyle.DashLine))
        for c in active:self.scene.addItem(ScreenItem(c,self))
        if not active:
            text=self.scene.addText('Your desk starts here.\nAdd a computer or import your Synergy layout.',QFont(self.font().family(),15));text.setDefaultTextColor(QColor(t['muted']))
        rect=self.scene.itemsBoundingRect().adjusted(-70,-100,70,100);self.scene.setSceneRect(rect)
        self.count_label.setText(f'{len(active)} computers')
        self.apply_btn.setEnabled(self.dirty);self.undo_btn.setEnabled(self.dirty or bool(self.backend.list_backups()))
        self.update_details();self.scene.update();QTimer.singleShot(10,self.fit)
    def fit(self):
        if self.scene.items():self.view.fitInView(self.scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
    def select(self,screen):self.selected=screen;self.update_details();self.scene.update()
    def selected_computer(self):return next((c for c in self.desk.computers if c.screen==self.selected),None)
    def update_details(self):
        c=self.selected_computer();self.edit_btn.setEnabled(bool(c));self.remove_btn.setEnabled(bool(c and not c.primary))
        self.detail_title.setText(c.label if c else 'Select a computer')
        self.detail_sub.setText(('Shares this desk’s keyboard and mouse' if c.primary else ', '.join(c.addresses) or 'Add an address in Edit to show connection status') if c else 'Windows and Linux share one desktop tile. Individual monitors are arranged in your operating system’s display settings.')
    def mark_dirty(self):self.dirty=True;self.apply_btn.setEnabled(True);self.undo_btn.setEnabled(True);self.footer.setText('Unsaved changes · Nothing changes on your desk until you apply.');self.refresh_computers()
    def confirm(self,title,text):return QMessageBox.question(self,title,text,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)==QMessageBox.StandardButton.Yes
    def apply_changes(self):
        if not self.dirty:return
        try:self.desk.validate()
        except Exception as e:self.message(str(e));return
        if not self.confirm('Apply this desk?','A backup will be saved, both selected OS profiles updated, and sharing briefly restarted. The layout will stay in place until you change it again.'):return
        self.apply_btn.setEnabled(False);self.message('Saving your desk and restarting sharing…')
        snapshot=copy.deepcopy(self.desk)
        def done(path):
            self.desk=snapshot;self.saved=copy.deepcopy(snapshot);self.dirty=False;self.render_desk();self.refresh_backups();self.footer.setText('Desk saved · Recovery point created');self.message('Your desk is saved. Connected computers will reconnect automatically.');self.refresh_status()
        self.work(lambda:self.backend.apply(snapshot),done)
    def undo(self):
        if self.dirty:self.desk=copy.deepcopy(self.saved);self.dirty=False;self.render_desk();self.refresh_computers();self.footer.setText('Unsaved changes discarded.');return
        self.go(3)
    def add_computer(self,checked=False,found=()):
        dialog=ComputerDialog(self,found=found)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        c=dialog.value
        if any(x.screen==c.screen for x in self.desk.computers):self.message('A computer with that screen name already exists.');return
        cells={(x.x,x.y) for x in self.desk.computers};c.x=max((p[0] for p in cells),default=-1)+1;c.y=0;c.primary=not bool(self.desk.computers)
        self.desk.computers.append(c);self.selected=c.screen;self.mark_dirty();self.render_desk();self.message('Computer added to your draft. Use Computers → Set up connection for a Linux laptop, then Apply changes.')
    def edit_selected(self):
        c=self.selected_computer()
        if not c:return
        dialog=ComputerDialog(self,c)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            v=dialog.value;c.label=v.label;c.addresses=v.addresses;c.username=v.username;c.platform=v.platform;self.mark_dirty();self.render_desk()
    def remove_selected(self):
        c=self.selected_computer()
        if not c or c.primary:return
        if self.confirm('Remove '+c.label+'?','This removes it from the desk layout. Synergy and its files remain on the computer. You can add it again later.'):
            self.desk.computers.remove(c);self.selected=None;self.mark_dirty();self.render_desk()
    def refresh_computers(self):
        if not hasattr(self,'computer_list'):return
        while self.computer_list.count():
            item=self.computer_list.takeAt(0)
            if item.widget():item.widget().deleteLater()
        for c in self.desk.computers:
            p=card();r=QHBoxLayout(p);r.setContentsMargins(18,16,18,16);text=QVBoxLayout();text.addWidget(label(c.label,'smallTitle'));text.addWidget(label(c.platform+'  ·  '+('Keyboard & mouse' if c.primary else ', '.join(c.addresses) or 'Address needed'),'muted'));r.addLayout(text,1)
            r.addWidget(button('Edit',lambda checked=False,n=c.screen:(self.select(n),self.edit_selected())))
            if not c.primary:
                r.addWidget(button('Reconnect',lambda checked=False,v=c:self.remote_reconnect(v)))
                r.addWidget(button('Set up connection',lambda checked=False,v=c:self.remote_setup(v)))
            self.computer_list.addWidget(p)
    def remote_reconnect(self,c):self.message('Reconnecting '+c.label+'…');self.work(lambda:self.backend.reconnect_remote(c),lambda out:self.message(out))
    def remote_setup(self,c):
        if c.platform!='Linux':self.message('For a Windows receiver, install Synergizer there and use Settings → Set up sharing → Receive.');return
        if not c.username or not c.addresses:self.select(c.screen);self.edit_selected();return
        self.message('Checking the identity of '+c.label+'…')
        def inspected(info):
            if not info['trusted']:
                warning='The host key has changed. Verify the new fingerprint on that computer before continuing.\n\n' if info['changed'] else 'Compare this fingerprint with the SSH host key on that computer before trusting it.\n\n'
                if not self.confirm('Trust '+c.label+'?',warning+info['fingerprint']+'\n\nTrust this computer for encrypted setup?'):return
                self.backend.trust_host(info)
            password,ok=QInputDialog.getText(self,'Pair '+c.label,'SSH password (leave blank to use your existing SSH key):',QLineEdit.EchoMode.Password)
            if not ok:return
            if not self.confirm('Configure '+c.label+'?','Back up its sharing settings, authorize Synergizer’s private pairing key, and configure automatic encrypted sharing at sign-in?'):return
            self.message('Pairing and configuring '+c.label+'…')
            def configure():
                self.backend.authorize_remote(c,password or None)
                return self.backend.configure_remote(c)
            self.work(configure,lambda out:self.message(out))
        self.work(lambda:self.backend.inspect_host(c),inspected)
    def find_computers(self):
        self.message('Looking for known computers and SSH-enabled devices on your local network…')
        networks=[]
        from PySide6.QtNetwork import QNetworkInterface
        import ipaddress
        for interface in QNetworkInterface.allInterfaces():
            if not (interface.flags() & QNetworkInterface.InterfaceFlag.IsUp) or interface.flags() & QNetworkInterface.InterfaceFlag.IsLoopBack:continue
            if any(s in interface.name().lower() for s in ('tailscale','docker','virbr','tun','veth','br-')):continue
            for entry in interface.addressEntries():
                address=entry.ip().toString()
                if '.' in address and not address.startswith(('127.','169.254.')):
                    try:
                        if ipaddress.ip_address(address).is_private:networks.append(str(ipaddress.ip_network(address+'/24',strict=False)))
                    except ValueError:pass
        def done(found):self.message(f'Found {len(found)} candidate computers. Choose one to add; discovery alone does not establish trust.');self.add_computer(found=found)
        self.work(lambda:self.backend.discover(networks),done)
    def refresh_status(self):
        if self.status_pending:return
        self.status_pending=True;snapshot=copy.deepcopy(self.desk)
        def done(statuses):
            self.status_pending=False;self.statuses=statuses
            count=sum(v in ('Connected','Running') for v in statuses.values());self.health_label.setText(f'{count} online · Updates automatically');self.recovery_status.setText('This computer: '+next((statuses.get(c.screen,'Unknown') for c in snapshot.computers if c.primary),'Not configured'));self.scene.update()
        # status() intentionally returns partial results if a device is unavailable.
        self.work(lambda:self.backend.status(snapshot),done)
    def reconnect(self):self.message('Restarting sharing…');self.work(self.backend.restart,lambda out:(self.message(out),self.refresh_status()))
    def show_logs(self):
        def done(text):
            d=QDialog(self);d.setWindowTitle('Sharing logs');d.resize(900,560);v=QVBoxLayout(d);edit=QPlainTextEdit(text);edit.setReadOnly(True);v.addWidget(edit);b=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);b.rejected.connect(d.reject);v.addWidget(b);d.exec()
        self.work(self.backend.logs,done)
    def export_diagnostics(self):
        path,_=QFileDialog.getSaveFileName(self,'Save sharing diagnostics','synergizer-diagnostics.txt','Text (*.txt)')
        if path:self.work(self.backend.logs,lambda text:(pathlib.Path(path).write_text(text),self.message('Diagnostics saved. Review them before sharing; logs may include computer names and addresses.')))
    def refresh_backups(self):
        if not hasattr(self,'backup_list'):return
        self.backup_list.clear()
        for path,meta in self.backend.list_backups():
            item=QListWidgetItem(meta['created'][:19].replace('T','  ')+'    '+meta['reason']);item.setData(Qt.ItemDataRole.UserRole,str(path));self.backup_list.addItem(item)
    def create_backup(self):self.work(lambda:self.backend.backup('Manual recovery point'),lambda out:(self.refresh_backups(),self.message('Recovery point saved.')))
    def restore_selected(self):
        item=self.backup_list.currentItem()
        if not item:self.message('Choose a backup first.');return
        if self.confirm('Restore this desk?','The current desk will be backed up before this recovery point is restored. Sharing will briefly restart.'):
            def done(desk):self.desk=desk;self.saved=copy.deepcopy(desk);self.dirty=False;self.render_desk();self.refresh_computers();self.refresh_backups();self.message('Your previous desk has been restored.')
            self.work(lambda:self.backend.restore(item.data(Qt.ItemDataRole.UserRole)),done)
    def import_existing(self):
        if self.dirty and not self.confirm('Replace your draft?','Discard unsaved changes and import the installed Synergy layout?'):return
        try:self.desk=self.backend.import_existing();self.mark_dirty();self.render_desk();self.message('Existing layout imported as a draft. Review it before applying.')
        except Exception as e:self.message(str(e))
    def import_profile(self):
        path,_=QFileDialog.getOpenFileName(self,'Import a desk profile','','Synergizer desk (*.json)')
        if not path:return
        try:self.desk=Desk.from_dict(json.loads(pathlib.Path(path).read_text()));self.mark_dirty();self.render_desk()
        except Exception as e:self.message('Could not import that profile: '+str(e))
    def export_profile(self):
        path,_=QFileDialog.getSaveFileName(self,'Export desk profile','my-desk.json','Synergizer desk (*.json)')
        if path:self.backend.export_profile(self.desk,path);self.message('Desk exported. It contains device names and addresses, but no passwords or private keys.')
    def setup_local(self):
        role,ok=QInputDialog.getItem(self,'Set up sharing','How will you use this computer?',['Share this computer’s keyboard and mouse','Receive keyboard and mouse from the desktop'],0,False)
        if not ok:return
        server=role.startswith('Share');default=next((c.screen for c in self.desk.computers if c.primary),'desktop') if server else __import__('socket').gethostname().split('.')[0]
        screen,ok=QInputDialog.getText(self,'Synergy identity','Stable screen name (use the same name for both desktop OSs):',text=default)
        if not ok or not SAFE_NAME.fullmatch(screen):return
        addresses=self.backend.settings.get('server_addresses',[])
        if not server and not addresses:
            text,ok=QInputDialog.getText(self,'Desktop address','Desktop IP address or host name:')
            if not ok or not text.strip():return
            addresses=[text.strip()]
        if not self.confirm('Configure automatic sharing?','This creates a backup, pauses Synergy’s normal layout manager, and configures sharing at sign-in. Keep Synergy installed and activated.'):return
        self.work(lambda:self.backend.setup_local('server' if server else 'client',screen,addresses,copy.deepcopy(self.desk)),lambda out:(self.message(out),self.refresh_status()))
    def closeEvent(self,event):
        if self.dirty and not self.confirm('Close without applying?','Your unsaved layout changes will be discarded. Existing sharing keeps running.'):
            event.ignore();return
        self.timer.stop();self.tray.hide();event.accept()
