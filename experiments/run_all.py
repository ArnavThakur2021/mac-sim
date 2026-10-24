"""Run compact, seeded sweeps and save raw CSV data and 300 dpi figures."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sim.csma_cd import simulate as cd
from sim.csma_ca import simulate as ca
from sim.bianchi import solve
from sim.hidden_terminal import compare

DATA=ROOT/'results/data'; PLOTS=ROOT/'results/plots'

def run(fast=False):
    DATA.mkdir(parents=True,exist_ok=True); PLOTS.mkdir(parents=True,exist_ok=True)
    seeds=range(2 if fast else 5); dur=.15 if fast else 1.0
    rows=[]; load_dur=dur if fast else .5
    for n in tqdm([2,5,10,15,20,30,40,50],desc='E1 stations'):
      for protocol,fn,opts in [('CSMA/CD',cd,{}),('CSMA/CA basic',ca,{}),('CSMA/CA RTS/CTS',ca,{'rts_cts':True})]:
       for seed in seeds:
        rows.append({'n':n,'protocol':protocol,**fn(n,dur,seed=seed,**opts)})
    df=pd.DataFrame(rows); df.to_csv(DATA/'stations.csv',index=False)
    for metric,title in [('throughput','Normalized throughput'),('mean_delay_s','Mean access delay (s)'),('collision_probability','Collision probability'),('fairness',"Jain's fairness")]:
      fig,ax=plt.subplots(figsize=(7,4))
      for p,g in df.groupby('protocol'):
       agg=g.groupby('n')[metric].agg(['mean','std','count']).fillna(0); ci=1.96*agg['std']/np.sqrt(agg['count'].clip(lower=1)); ax.errorbar(agg.index,agg['mean'],yerr=ci,marker='o',capsize=3,label=p)
      ax.set(xlabel='Number of stations',ylabel=title,title=f'E1: {title} vs station count'); ax.grid(alpha=.3); ax.legend(); fig.tight_layout(); fig.savefig(PLOTS/f'e1_{metric}.png',dpi=300); plt.close(fig)
    fig,axs=plt.subplots(2,2,figsize=(10,7))
    for ax,(metric,title) in zip(axs.flat,[('throughput','Throughput'),('mean_delay_s','Mean delay (s)'),('collision_probability','Collision probability'),('fairness',"Jain's fairness")]):
      for p,g in df.groupby('protocol'):
       agg=g.groupby('n')[metric].mean(); ax.plot(agg.index,agg.values,marker='o',label=p)
      ax.set(title=title,xlabel='Stations'); ax.grid(alpha=.25)
    axs[0,0].legend(fontsize=7); fig.suptitle('E1: MAC protocol comparison'); fig.tight_layout(); fig.savefig(PLOTS/'e1_combined.png',dpi=300); plt.close(fig)
    rows=[]
    for n in [10,30]:
     for load in np.linspace(.1,1.5,8 if fast else 15):
      # offered packets/s per station; scale from nominal CA service rate
      rate=load*1_000_000/8184/n
      for p,fn,opt in [('CD',cd,{}),('CA',ca,{})]:
       for seed in seeds:
        x=fn(n,load_dur,seed=seed,saturated=False,arrival_rate_pps=rate,**opt); rows.append({'n':n,'load':load,'protocol':p,'seed':seed,**x})
    load_df=pd.DataFrame(rows); load_df.to_csv(DATA/'load.csv',index=False)
    for metric,ylab in [('throughput','Normalized throughput'),('mean_delay_s','Mean access delay (s)')]:
      fig,ax=plt.subplots(figsize=(7,4))
      for (n,p),g in load_df.groupby(['n','protocol']): ax.plot(g.load,g[metric],marker='o',label=f'N={n} {p}')
      ax.set(xlabel='Offered load (fraction of nominal capacity)',ylabel=ylab,title=f'E2: {ylab} vs load'); ax.grid(alpha=.3); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(PLOTS/f'e2_{metric}.png',dpi=300); plt.close(fig)
    rows=[]
    for n in [10,40]:
     for cw in [8,16,32,64,128]:
      for seed in seeds:
       rows.append({'n':n,'cw_min':cw,**ca(n,dur,seed=seed,cw_min=cw)})
    cw_df=pd.DataFrame(rows); cw_df.to_csv(DATA/'cw.csv',index=False)
    fig,ax=plt.subplots(figsize=(7,4))
    for n,g in cw_df.groupby('n'): ax.plot(g.cw_min,g.throughput,marker='o',label=f'N={n}')
    ax.set(xlabel='CWmin (choices)',ylabel='Normalized throughput',title='E3: Contention-window sweep'); ax.set_xscale('log',base=2); ax.grid(alpha=.3); ax.legend(); fig.tight_layout(); fig.savefig(PLOTS/'e3_cw.png',dpi=300); plt.close(fig)
    rows=[]
    for bits in [256,512,1024,2048,4096,8184,12000]:
     for rts in [False,True]:
      for seed in seeds: rows.append({'payload_bits':bits,'rts_cts':rts,'seed':seed,**ca(10,dur,seed=seed,payload_bits=bits,rts_cts=rts)})
    payload_df=pd.DataFrame(rows); payload_df.to_csv(DATA/'payload.csv',index=False)
    fig,ax=plt.subplots(figsize=(7,4))
    for rts,g in payload_df.groupby('rts_cts'): ax.plot(g.payload_bits,g.throughput,marker='o',label='RTS/CTS' if rts else 'Basic')
    ax.set(xlabel='Payload (bits)',ylabel='Normalized throughput',title='E4: Payload size and RTS/CTS'); ax.grid(alpha=.3); ax.legend(); fig.tight_layout(); fig.savefig(PLOTS/'e4_payload.png',dpi=300); plt.close(fig)
    rows=[]
    for pairs in [1,2,3,5,8,10]:
     for rts in [False,True]:
      for seed in seeds: rows.append({'hidden_pairs':pairs,'rts_cts':rts,'seed':seed,**compare(pairs,dur,seed=seed,rts_cts=rts)})
    hidden_df=pd.DataFrame(rows); hidden_df.to_csv(DATA/'hidden.csv',index=False)
    fig,ax=plt.subplots(figsize=(7,4))
    for rts,g in hidden_df.groupby('rts_cts'): ax.plot(g.hidden_pairs,g.collision_probability,marker='o',label='RTS/CTS' if rts else 'Basic')
    ax.set(xlabel='Hidden sender pairs',ylabel='Collision probability',title='E5: Hidden-terminal collisions'); ax.grid(alpha=.3); ax.legend(); fig.tight_layout(); fig.savefig(PLOTS/'e5_hidden.png',dpi=300); plt.close(fig)
    rows=[]
    for n in range(2,51,2):
     for rts in [False,True]:
      analytic=solve(n,rts_cts=rts)
      sim=ca(n,5.0,seed=11,rts_cts=rts)
      rows.append({'n':n,'rts_cts':rts,'analytic':analytic['throughput'],'simulated':sim['throughput'],'error_pct':100*abs(sim['throughput']-analytic['throughput'])/analytic['throughput']})
    val=pd.DataFrame(rows); val.to_csv(DATA/'validation.csv',index=False)
    fig,ax=plt.subplots(figsize=(7,4))
    for rts,g in val.groupby('rts_cts'):
      label='RTS/CTS' if rts else 'Basic'; ax.plot(g.n,g.analytic,label=f'{label} analytical'); ax.plot(g.n,g.simulated,'o',label=f'{label} simulated')
    ax.set(xlabel='Stations',ylabel='Normalized throughput',title='E6: Bianchi validation'); ax.grid(alpha=.3); ax.legend(); fig.tight_layout(); fig.savefig(PLOTS/'e6_validation.png',dpi=300); plt.close(fig)
    # E7: textbook Ethernet approximation alongside a propagation-sensitive model sweep.
    rows=[]
    for prop_us in [1,2,5,10,20,50]:
     from dataclasses import replace
     from config import CD as CDC
     c=replace(CDC,propagation_s=prop_us*1e-6)
     x=cd(10,dur,seed=13,config=c); a=c.propagation_s/(max(c.min_frame_bytes*8,8184+64)/c.rate_bps)
     rows.append({'propagation_us':prop_us,'simulated_throughput':x['throughput'],'classic_efficiency':1/(1+6.44*a)})
    prop=pd.DataFrame(rows); prop.to_csv(DATA/'propagation.csv',index=False)
    fig,ax=plt.subplots(figsize=(7,4)); ax.plot(prop.propagation_us,prop.simulated_throughput,'o-',label='CSMA/CD simulation'); ax.plot(prop.propagation_us,prop.classic_efficiency,'--',label='1/(1+6.44a)'); ax.set(xlabel='Propagation delay (µs)',ylabel='Efficiency / normalized throughput',title='E7: Propagation delay effect'); ax.grid(alpha=.3); ax.legend(); fig.tight_layout(); fig.savefig(PLOTS/'e7_propagation.png',dpi=300); plt.close(fig)
    print('\nValidation mean absolute error: %.2f%%' % val.error_pct.mean())
    print('\nStation sweep summary (averaged seeds):')
    print(df.groupby(['n','protocol']).throughput.mean().round(4).to_string())
    print('\nGenerated CSV files:',len(list(DATA.glob('*.csv'))),'plots:',len(list(PLOTS.glob('*.png'))))
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--fast',action='store_true'); run(p.parse_args().fast)
