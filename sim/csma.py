"""Carrier-sense baseline without collision detection.

This educational baseline waits for the whole frame interval to learn that a
simultaneous transmission failed. CSMA/CD can abort at collision detection;
CSMA/CA instead uses DCF and acknowledgements.
"""
import numpy as np
from config import CD
from .common import metric_summary

def simulate(n_stations=10,duration_s=1.0,seed=1,payload_bits=None,config=CD,
             record_trace=False,trace_limit=300):
    rng=np.random.default_rng(seed); n=n_stations; bits=payload_bits or config.payload_bits
    frame_s=max(config.min_frame_bytes*8,bits+64)/config.rate_bps
    frame_time=frame_s+config.ifg_s; t=0.; cw=config.slot_s
    counters=rng.integers(0,config.max_backoff_stage+1,n); stages=np.zeros(n,int)
    successes=[0]*n; delays=[]; born=np.zeros(n); attempts=collisions=drops=0; succ_t=coll_t=idle_t=0.; trace=[]
    def remember(kind, involved=(), detail='', duration=0.):
        if not record_trace or len(trace)>=trace_limit: return
        involved=set(map(int,involved)); states=[]
        for i in range(n):
            if i in involved: states.append(kind)
            else: states.append(f'backoff {int(counters[i])}')
        trace.append({'time_s':float(t),'duration_s':float(duration),'kind':kind,
                      'stations':sorted(involved),'detail':detail,'states':states,
                      'backoff':counters.astype(int).tolist(),'stage':stages.astype(int).tolist()})
    while t<duration_s:
        ready=np.flatnonzero(counters==0)
        if len(ready)==1:
            i=int(ready[0]); remember('success',[i],'Sense idle → send DATA; channel releases after frame + IFG.',frame_time)
            attempts+=1; successes[i]+=1; delays.append(t+frame_time-born[i]); succ_t+=frame_time; t+=frame_time
            born[i]=t
            stages[i]=0; counters[i]=int(rng.integers(0,config.max_backoff_stage+1))
        elif len(ready)>1:
            # Unlike CD, stations spend the entire frame interval before learning
            # that the receiver could not decode their overlapping transmissions.
            remember('collision',ready,'Overlap lasts to frame end; failure is learned after full frame airtime.',frame_time)
            attempts+=len(ready); collisions+=len(ready); coll_t+=frame_time; t+=frame_time
            for i in ready:
                stages[i]=min(stages[i]+1,config.max_backoff_stage)
                window=min(2**stages[i],2**config.max_backoff_stage)
                counters[i]=int(rng.integers(0,window))
        else:
            waiting=np.flatnonzero(counters>0)
            remember('carrier sense',waiting,'Channel idle; backoff counters decrement.',config.slot_s)
            idle_t+=config.slot_s; t+=config.slot_s
            counters[waiting]-=1
    total=max(succ_t+coll_t+idle_t,1e-15); scale=duration_s/total
    result=metric_summary(payload_bits=bits,rate_bps=config.rate_bps,elapsed_s=duration_s,
      successes=successes,delays=delays,attempts=attempts,collisions=collisions,drops=drops,
      success_s=succ_t*scale,collision_s=coll_t*scale,idle_s=idle_t*scale)
    if record_trace: result['trace']=trace
    return result
