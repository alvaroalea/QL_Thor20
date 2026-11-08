#!/usr/bin/env python3
# sim_u13.py - asynchronous model of the U13 equations (U13.pld) against a
# simple SCSI target, to check selection, read, write and selection timeout.
# Usage: python3 sim_u13.py
# Asynchronous model of the U13 equations + a SCSI target, to check the handshake.
def gal(s):
    # inputs: DISC, A4, A3, RW, DSn (bus /DS), REQn, BSYn, SELTO, RESETn ; feedback: GO, RDP, ACKO
    DATA = s['DISC'] and not s['A4'] and not s['A3'] and not s['DSn']
    CTRL = s['DISC'] and not s['A4'] and s['A3'] and not s['DSn']
    REQa = not s['REQn']; R = s['RESETn']
    GO  = R and ((DATA and REQa and not s['ACKO']) or (DATA and s['GO']))
    RDP = R and ((DATA and s['RW'] and s['GO']) or (s['RDP'] and REQa))
    ACKO = R and ((DATA and not s['RW'] and s['GO']) or (s['RDP'] and not DATA) or (s['ACKO'] and REQa))
    SELO = R and CTRL and not s['RW'] and s['BSYn'] and not s['SELTO']
    HOLD = (DATA and not s['GO']) or (DATA and not s['RW'] and s['GO'] and REQa) or \
           (CTRL and not s['RW'] and s['BSYn'] and not s['SELTO'])
    U12 = DATA or (CTRL and not s['RW'])
    U15 = CTRL and s['RW']
    return dict(GO=GO, RDP=RDP, ACKO=ACKO, SELO=SELO, HOLD=HOLD, U12=U12, U15=U15)

def settle(s):
    for _ in range(20):
        o = gal(s); ch = any(s.get(k) != o[k] for k in ('GO','RDP','ACKO'))
        s.update(o)
        if not ch: return
    raise Exception('oscillation')

class Target:
    def __init__(s, data_in): s.q=list(data_in); s.got=[]; s.state='idle'
    def step(s, st, bus):
        if s.state=='idle':
            if st['SELO'] and bus==0x01: st['BSYn']=False; s.state='sel'
        elif s.state=='sel':
            if not st['SELO']: s.state='req'
        elif s.state=='req':
            if s.q or s.mode=='out': st['REQn']=False; s.state='wack'
        elif s.state=='wack':
            if st['ACKO']:
                if s.mode=='out': s.got.append(bus)
                else: s.q.pop(0)
                st['REQn']=True; s.state='wnack'
        elif s.state=='wnack':
            if not st['ACKO']: s.state='req' if (s.q or s.mode=='out') else 'done'

def cpu_cycle(st, tgt, a3, rw, wdata=None, maxsteps=1000):
    st.update(A3=a3, RW=rw, DSn=False); settle(st)
    for n in range(maxsteps):
        bus = wdata if (st['U12'] and not rw) else 0
        tgt.step(st, bus); settle(st)
        if not st['HOLD']: break
    else: raise Exception('cpu hung')
    val = (tgt.q[0] if (rw and st['U12'] and tgt.q) else None)
    st['DSn']=True; settle(st)
    for _ in range(3): tgt.step(st, 0); settle(st)   # gap between CPU cycles
    return val

base=dict(DISC=True,A4=False,A3=False,RW=True,DSn=True,REQn=True,BSYn=True,SELTO=False,RESETn=True,GO=False,RDP=False,ACKO=False)
# read test
st=dict(base); t=Target([0x11,0x22,0x33,0x44]); t.mode='in'
cpu_cycle(st,t,1,False,0x01); got=[cpu_cycle(st,t,0,True) for _ in range(4)]
print('read  ', [hex(x) for x in got], 'target state', t.state)
# write test
st=dict(base); t=Target([]); t.mode='out'
cpu_cycle(st,t,1,False,0x01); [cpu_cycle(st,t,0,False,v) for v in (0x08,0,0,1,1,0)]
print('write ', [hex(x) for x in t.got])
# selection timeout (no target answers)
st=dict(base); st.update(A3=True,RW=False,DSn=False); settle(st); print('sel wait hold=',st['HOLD'],'SEL=',st['SELO'])
st['SELTO']=True; settle(st); print('after RC timeout hold=',st['HOLD'],'SEL=',st['SELO'])
