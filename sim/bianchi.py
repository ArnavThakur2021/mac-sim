"""Bianchi saturated DCF fixed-point model."""
from scipy.optimize import brentq
from config import CA
from .csma_ca import durations

def solve(n_stations, rts_cts=False, payload_bits=None, cw_min=None, max_stage=None, config=CA):
    """Return tau, p and normalized throughput using Bianchi's renewal model."""
    n=n_stations; w=cw_min or config.cw_min; m=config.max_stage if max_stage is None else max_stage
    def tau_of(p):
        den=(1-2*p)*(w+1)+p*w*(1-(2*p)**m)
        return 2*(1-2*p)/den if abs(den)>1e-14 else 0.0
    def f(p): return p-(1-(1-tau_of(p))**(n-1))
    p=brentq(f,0.0,0.999999)
    tau=tau_of(p); ptr=1-(1-tau)**n
    ps=n*tau*(1-tau)**(n-1)/ptr if ptr else 0
    ts,tc,sigma=durations(payload_bits or config.payload_bits,config,rts_cts)
    # Renewal slots include each idle slot; P_s P_tr is the probability of a successful slot.
    den=(1-ptr)*sigma+ptr*ps*ts+ptr*(1-ps)*tc
    s=ps*ptr*(payload_bits or config.payload_bits)/config.rate_bps/den
    return {"n_stations":n,"tau":tau,"collision_probability":p,"p_success_given_busy":ps,"throughput":s}
