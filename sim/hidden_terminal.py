"""Topology-aware hidden-terminal experiment for senders around one AP."""
import numpy as np
from config import CA
from .common import metric_summary
from .csma_ca import backoff_window, durations

def carrier_sense_matrix(n_senders: int, hidden_fraction: float = 1.0):
    """Return a symmetric sensing graph; deterministic ring-distance topology."""
    matrix=np.ones((n_senders,n_senders),dtype=bool); np.fill_diagonal(matrix,False)
    hidden=max(0,min(n_senders,int(round(hidden_fraction*(n_senders-1)))))
    for i in range(n_senders):
        for j in range(i+1,n_senders):
            if (j-i) % n_senders <= hidden//2 or (i-j) % n_senders <= hidden//2:
                matrix[i,j]=matrix[j,i]=False
    return matrix

def compare(n_hidden_pairs=1,duration_s=1.0,seed=1,rts_cts=False,hidden_fraction=1.0,payload_bits=None,config=CA,**kwargs):
    """Simulate senders outside one another's sensing range, all targeting AP B.

    A data overlap at B loses every overlapping frame. RTS/CTS reserves the
    receiver neighborhood: the AP CTS is heard by otherwise-hidden senders.
    """
    n=max(2,2*n_hidden_pairs); rng=np.random.default_rng(seed); bits=payload_bits or config.payload_bits
    graph=carrier_sense_matrix(n,hidden_fraction); cw=config.cw_min
    ts,tc,sigma=durations(bits,config,rts_cts); counters=rng.integers(0,cw,n); stage=np.zeros(n,int)
    t=idle=succ=coll=0.; successes=[0]*n; attempts=collisions=0; delays=[]; born=np.zeros(n); nav_until=0.
    while t<duration_s:
        active=np.flatnonzero(counters==0)
        if t<nav_until: active=np.array([],dtype=int)
        elif len(active)>1:
            # Stations sensing one another defer to the first; mutually hidden
            # senders launch together and collide at the common receiver.
            kept=[]
            for i in active:
                if not any(graph[i,j] for j in kept): kept.append(i)
            active=np.asarray(kept,dtype=int)
        if not len(active):
            idle+=sigma; t+=sigma; counters=np.maximum(0,counters-1); continue
        attempts+=len(active)
        if len(active)>1:
            collisions+=len(active); coll+=tc; t+=tc
            for i in active:
                stage[i]=min(stage[i]+1,config.max_stage); counters[i]=rng.integers(0,backoff_window(cw,stage[i],config.max_stage))
        else:
            i=int(active[0]); successes[i]+=1; delays.append(t+ts-born[i]); succ+=ts; t+=ts
            stage[i]=0; counters[i]=rng.integers(0,cw)
    elapsed=duration_s; scale=elapsed/max(succ+coll+idle,1e-15)
    return metric_summary(payload_bits=bits,rate_bps=config.rate_bps,elapsed_s=elapsed,successes=successes,delays=delays,attempts=attempts,collisions=collisions,drops=0,success_s=succ*scale,collision_s=coll*scale,idle_s=idle*scale)
