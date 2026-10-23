from __future__ import annotations
from dataclasses import dataclass, field, asdict
import re, uuid

SAFE_NAME=re.compile(r'^[A-Za-z0-9_.-]{1,100}$')
@dataclass
class Computer:
    screen: str
    label: str
    x: int = 0
    y: int = 0
    primary: bool = False
    addresses: list[str] = field(default_factory=list)
    username: str = ''
    platform: str = 'Linux'
    options: list[str] = field(default_factory=list)
    enabled: bool = True

@dataclass
class Desk:
    computers: list[Computer] = field(default_factory=list)
    options: list[str] = field(default_factory=lambda:['heartbeat = 5000','relativeMouseMoves = true','clipboardSharing = false'])
    revision: str = field(default_factory=lambda:uuid.uuid4().hex)
    title: str = 'My everyday desk'
    def to_dict(self): return {'schema':1,**asdict(self)}
    @classmethod
    def from_dict(cls,d):
        if d.get('schema')!=1: raise ValueError('This profile version is not supported.')
        return cls([Computer(**v) for v in d['computers']],d.get('options',[]),d['revision'],d.get('title','My everyday desk'))
    def validate(self):
        active=[c for c in self.computers if c.enabled]
        for c in self.computers:
            if not isinstance(c.x,int) or not isinstance(c.y,int) or abs(c.x)>50 or abs(c.y)>50:raise ValueError('Computer positions must stay within the desk grid.')
            if any(not isinstance(v,str) or '\n' in v or '\r' in v for v in c.options):raise ValueError('Invalid screen option in this profile.')
        if any(not isinstance(v,str) or '\n' in v or '\r' in v for v in self.options):raise ValueError('Invalid layout option in this profile.')
        if not active: raise ValueError('Add at least one computer to your desk.')
        if len([c for c in active if c.primary])!=1: raise ValueError('Choose exactly one computer to share its keyboard and mouse.')
        names=[c.screen for c in active]
        if len(set(names))!=len(names):raise ValueError('Every computer needs a different Synergy screen name.')
        if any(not SAFE_NAME.fullmatch(n) for n in names):raise ValueError('Screen names may contain letters, numbers, periods, hyphens and underscores.')
        cells={(c.x,c.y) for c in active}
        if len(cells)!=len(active):raise ValueError('Two computers occupy the same position. Drag them into separate spaces.')
        seen={next(iter(cells))}
        while True:
            added={p for p in cells if any(abs(p[0]-q[0])+abs(p[1]-q[1])==1 for q in seen)}-seen
            if not added:break
            seen|=added
        if seen!=cells:raise ValueError('Bring your computers together: each one must be beside, above or below another.')
    def compile(self):
        self.validate()
        active=[c for c in self.computers if c.enabled]
        out=['section: screens']
        for c in active:
            out.append(f'\t{c.screen}:');out.extend('\t\t'+v for v in c.options)
        out+=['end','','section: links']
        for c in active:
            out.append(f'\t{c.screen}:')
            for direction,dx,dy in [('left',-1,0),('right',1,0),('up',0,-1),('down',0,1)]:
                for other in active:
                    if (other.x,other.y)==(c.x+dx,c.y+dy):out.append(f'\t\t{direction} = {other.screen}')
        out+=['end','','section: options',*['\t'+v for v in self.options],'end','']
        return '\n'.join(out)

def parse_layout(text:str, primary:str='')->Desk:
    sections={};section=None
    for raw in text.splitlines():
        line=raw.strip()
        if line.startswith('section: '):section=line.split(':',1)[1].strip();sections[section]=[]
        elif line=='end':section=None
        elif section and line and not line.startswith('#'):sections[section].append((raw,line))
    if set(sections)-{'screens','links','options'}:raise ValueError('This layout uses aliases or hotkeys. Export a backup and simplify it before importing; Synergizer will not discard these settings.')
    comps={};current=None
    for raw,line in sections.get('screens',[]):
        if line.endswith(':'):
            current=line[:-1];comps[current]=Computer(current,current,primary=current==primary)
        elif current:comps[current].options.append(line)
    links=[];current=None
    for raw,line in sections.get('links',[]):
        if line.endswith(':'):current=line[:-1]
        elif '=' in line and current:
            a,b=[v.strip() for v in line.split('=',1)]
            # V1 preserves full-edge links. Reject partial links rather than losing them.
            if '(' in a or '(' in b:
                a=a.replace('(0,100)','');b=b.replace('(0,100)','')
                if '(' in a or '(' in b:raise ValueError('This desk uses partial-edge links. Keep the existing layout; this editor currently supports full-edge connections.')
            if a in ('left','right','up','down') and b in comps:links.append((current,a,b))
            else:raise ValueError('A screen link could not be imported safely.')
    positions={}
    delta={'left':(-1,0),'right':(1,0),'up':(0,-1),'down':(0,1)}
    for root in comps:
        if root in positions:continue
        positions[root]=(len(positions)*2,0);pending=[root]
        while pending:
            n=pending.pop()
            for a,d,b in links:
                if a!=n:continue
                dx,dy=delta[d];p=(positions[a][0]+dx,positions[a][1]+dy)
                if b not in positions:positions[b]=p;pending.append(b)
                elif positions[b]!=p:raise ValueError('This layout wraps or has inconsistent links; it cannot be edited safely in this version.')
    if comps and not any(c.primary for c in comps.values()):next(iter(comps.values())).primary=True
    for n,c in comps.items():c.x,c.y=positions[n]
    return Desk(list(comps.values()),[line for _,line in sections.get('options',[])])
