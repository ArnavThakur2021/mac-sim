"""Slot-based IEEE 802.11 DCF model with basic and RTS/CTS access."""
import numpy as np
from config import CA
from .common import metric_summary

def backoff_window(cw_min, stage, max_stage=5):
    """Return the number of choices in [0,CW-1], capped at stage m."""
    return min(cw_min * (2 ** min(stage, max_stage)), cw_min * (2 ** max_stage))

def durations(payload_bits, config=CA, rts_cts=False):
    """Return (success, collision, idle-slot) durations in seconds."""
    d=lambda b: b/config.rate_bps
    data=d(payload_bits+config.mac_header_bits+config.phy_header_bits)
    ack=d(config.ack_bits+config.phy_header_bits)
    if rts_cts:
        rts=d(config.rts_bits+config.phy_header_bits); cts=d(config.cts_bits+config.phy_header_bits)
        return (rts+config.sifs_s+cts+config.sifs_s+data+config.sifs_s+ack+config.difs_s+4*config.propagation_s,
                rts+config.difs_s+config.propagation_s, config.slot_s)
    return (data+config.sifs_s+ack+config.difs_s+2*config.propagation_s,
            data+config.difs_s+config.propagation_s, config.slot_s)

def simulate(n_stations=10, duration_s=1.0, seed=1, saturated=True,
             arrival_rate_pps=0.0, payload_bits=None, cw_min=None,
             max_stage=None, retry_limit=None, rts_cts=False, config=CA):
    """Run DCF. Busy periods freeze counters; each busy period is followed by DIFS."""
    rng=np.random.default_rng(seed); n=n_stations; bits=payload_bits or config.payload_bits
    cw=cw_min or config.cw_min; m=config.max_stage if max_stage is None else max_stage
    retry=config.retry_limit if retry_limit is None else retry_limit
    ts,tc,sigma=durations(bits,config,rts_cts)
    t=0.; counters=np.array([rng.integers(0,cw) for _ in range(n)],dtype=int)
    stages=np.zeros(n,dtype=int); tries=np.zeros(n,dtype=int); queued=np.full(n,saturated,dtype=bool)
    born=np.zeros(n); successes=[0]*n; delays=[]; attempts=collisions=drops=0
    st=ct=it=0.; idle_since=0.
    while t<duration_s:
        if not saturated:
            for i in range(n):
                if not queued[i] and rng.random()<1-np.exp(-arrival_rate_pps*sigma):
                    queued[i]=True; born[i]=t; counters[i]=rng.integers(0,cw); stages[i]=tries[i]=0
        active=np.flatnonzero(queued)
        if len(active)==0:
            t+=sigma; it+=sigma; idle_since+=sigma; continue
        # Backoff slots elapse only following a DIFS-length idle period.
        if idle_since < config.difs_s:
            step=min(sigma,config.difs_s-idle_since); t+=step; it+=step; idle_since+=step; continue
        ready=active[counters[active]==0]
        if len(ready)==0:
            counters[active]-=1; t+=sigma; it+=sigma; idle_since+=sigma; continue
        attempts+=len(ready)
        if len(ready)==1:
            i=int(ready[0]); successes[i]+=1; delays.append(t+ts-born[i]); st+=ts; t+=ts
            queued[i]=saturated; stages[i]=tries[i]=0
            if queued[i]: born[i]=t; counters[i]=rng.integers(0,cw)
        else:
            collisions+=len(ready); ct+=tc; t+=tc
            for i in ready:
                i=int(i); tries[i]+=1; stages[i]=min(stages[i]+1,m)
                if tries[i]>retry: drops+=1; queued[i]=saturated; tries[i]=0; stages[i]=0
                if queued[i]: counters[i]=rng.integers(0,backoff_window(cw,stages[i],m))
        idle_since=0.
    elapsed=duration_s; accounted=st+ct+it; scale=elapsed/max(accounted,1e-15)
    return metric_summary(payload_bits=bits,rate_bps=config.rate_bps,elapsed_s=elapsed,
      successes=successes,delays=delays,attempts=attempts,collisions=collisions,drops=drops,
      success_s=st*scale,collision_s=ct*scale,idle_s=it*scale)
