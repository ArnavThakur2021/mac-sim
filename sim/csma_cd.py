"""Slot-based 1-persistent CSMA/CD educational simulator."""
import numpy as np
from config import CD
from .common import metric_summary

def simulate(n_stations=10, duration_s=1.0, seed=1, saturated=True,
             arrival_rate_pps=0.0, payload_bits=None, config=CD,
             record_trace=False, trace_limit=300):
    """Simulate Ethernet attempts with busy periods and binary exponential backoff.

    Poisson arrivals use one-frame queues. A collision consumes propagation
    detection time plus jam time; successful frames consume frame time and IFG.
    """
    rng = np.random.default_rng(seed); n = n_stations
    bits = payload_bits or config.payload_bits
    frame_s = max(config.min_frame_bytes * 8, bits + 64) / config.rate_bps
    busy_s = frame_s + config.ifg_s
    t = 0.0; backoff = np.zeros(n, dtype=int); stage = np.zeros(n, dtype=int)
    queued = np.full(n, saturated, dtype=bool); arrival = np.zeros(n)
    attempts = collisions = drops = 0; successes = [0]*n; delays=[]
    succ_t = coll_t = idle_t = 0.0; trace=[]
    def remember(kind, involved=(), detail='', duration=0.0):
        if not record_trace or len(trace)>=trace_limit: return
        involved=set(map(int,involved)); states=[]
        for station in range(n):
            if station in involved: states.append(kind)
            elif queued[station]: states.append(f'backoff {int(backoff[station])}')
            else: states.append('idle')
        trace.append({'time_s':float(t),'duration_s':float(duration),'kind':kind,
                      'stations':sorted(involved),'detail':detail,'states':states,
                      'backoff':backoff.astype(int).tolist(),'stage':stage.astype(int).tolist()})
    while t < duration_s:
        if not saturated:
            for i in range(n):
                if not queued[i] and rng.random() < 1-np.exp(-arrival_rate_pps*config.slot_s):
                    queued[i] = True; arrival[i] = t
                    backoff[i] = int(rng.integers(0, max(1, 2**min(stage[i],config.max_backoff_stage))))
        ready = np.flatnonzero(queued & (backoff == 0))
        if len(ready) == 1:
            i=int(ready[0]); remember('success',[i],'Carrier clear → DATA → IFG.',busy_s); attempts+=1; successes[i]+=1; delays.append(t+busy_s-arrival[i]); succ_t+=busy_s; t+=busy_s
            stage[i]=0; queued[i]=saturated
            if queued[i]: backoff[i]=0
        elif len(ready)>1:
            attempts+=len(ready); collisions+=len(ready)
            ctime=max(config.slot_s, 2*config.propagation_s + config.jam_bits/config.rate_bps)
            remember('collision',ready,'Collision detected; send JAM, then binary exponential backoff.',ctime)
            coll_t+=ctime; t+=ctime
            for i in ready:
                stage[i]+=1
                if stage[i]>=config.retry_limit:
                    drops+=1; stage[i]=0; queued[i]=saturated
                backoff[i]=int(rng.integers(0,2**min(stage[i],config.max_backoff_stage)))
        else:
            remember('carrier sense',queued & (backoff>0),'Channel idle; waiting stations decrement backoff.',config.slot_s)
            idle_t+=config.slot_s; t+=config.slot_s
            backoff[queued & (backoff>0)]-=1
    elapsed=min(t,duration_s) if t>duration_s else t
    # Normalize channel accounting to wall-clock horizon to include truncated final event.
    elapsed=duration_s
    scale=duration_s/max(succ_t+coll_t+idle_t,1e-15)
    result=metric_summary(payload_bits=bits,rate_bps=config.rate_bps,elapsed_s=elapsed,
      successes=successes,delays=delays,attempts=attempts,collisions=collisions,drops=drops,
      success_s=succ_t*scale,collision_s=coll_t*scale,idle_s=idle_t*scale)
    if record_trace: result['trace']=trace
    return result
