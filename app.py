"""Interactive dashboard for the MAC simulation course project."""
from pathlib import Path
import sys
import pandas as pd
import streamlit as st
ROOT=Path(__file__).resolve().parent; sys.path.insert(0,str(ROOT))
from sim.csma_cd import simulate as cd
from sim.csma_ca import simulate as ca
from sim.hidden_terminal import compare
from sim.bianchi import solve

st.set_page_config(page_title='MAC Performance Lab',page_icon='📡',layout='wide')
st.title('CSMA Performance Lab')
st.caption('A reproducible, slot-based exploration of shared-medium access.')
tabs=st.tabs(['Overview','Live simulator','Comparison','Hidden terminal','Bianchi validation','Results gallery'])
with tabs[0]:
 st.markdown('### Why two access methods?\nEthernet detects a collision while transmitting and backs off. Wi-Fi cannot reliably listen while transmitting, so DCF avoids collisions with randomized backoff, ACKs, and optional RTS/CTS.')
 st.dataframe(pd.DataFrame([['Medium','Wired','Wireless'],['Collision response','Detect and abort','Infer from missing ACK'],['Coordination','Carrier sense','Carrier sense plus NAV'],['ACK','No in classic Ethernet','Yes']],columns=['Dimension','CSMA/CD','CSMA/CA']),hide_index=True)
with tabs[1]:
 n=st.sidebar.slider('Stations',1,50,10); seconds=st.sidebar.slider('Duration (s)',.05,2.,.25); proto=st.sidebar.selectbox('Protocol',['CSMA/CA','CSMA/CD']); rts=st.sidebar.checkbox('RTS/CTS',False); payload=st.sidebar.slider('Payload (bits)',256,12000,8184,256); seed=st.sidebar.number_input('Seed',0,100000,7)
 if st.button('Run simulation'):
  result=(ca if proto=='CSMA/CA' else cd)(n,seconds,seed=int(seed),payload_bits=payload,rts_cts=rts if proto=='CSMA/CA' else False)
  cols=st.columns(4)
  for col,label,key in zip(cols,['Throughput','Mean delay','Collision probability','Fairness'],['throughput','mean_delay_s','collision_probability','fairness']): col.metric(label,f"{result[key]:.4f}")
  st.json({k:v for k,v in result.items() if k not in ('per_station_successes','per_station_throughput')})
with tabs[2]:
 n2=st.slider('Stations for comparison',2,50,10,key='cmpn'); d=st.slider('Duration',.05,2.,.25,key='cmpd')
 if st.button('Compare CD and CA'):
  a=cd(n2,d); b=ca(n2,d); st.dataframe(pd.DataFrame([{'Protocol':'CSMA/CD',**a},{'Protocol':'CSMA/CA',**b}]).set_index('Protocol')[['throughput','mean_delay_s','collision_probability','fairness']])
with tabs[3]:
 pairs=st.slider('Hidden sender pairs',1,10,2); d=st.slider('Duration',.05,2.,.25,key='hd')
 if st.button('Run hidden-terminal comparison'):
  st.dataframe(pd.DataFrame([{'Access':'Basic',**compare(pairs,d,seed=9)},{'Access':'RTS/CTS',**compare(pairs,d,seed=9,rts_cts=True)}]).set_index('Access')[['throughput','collision_probability','collision_fraction']])
 st.caption('Topology approximation: pairs compete at a common receiver; see report limitations.')
with tabs[4]:
 ns=list(range(2,51,2)); frame=pd.DataFrame([{'Stations':n,'Analytical':solve(n)['throughput']} for n in ns]); st.line_chart(frame.set_index('Stations'))
with tabs[5]:
 for f in sorted((ROOT/'results/plots').glob('*.png')):
  st.image(str(f),caption=f.stem)
 for f in sorted((ROOT/'results/data').glob('*.csv')):
  st.download_button(f'Download {f.name}',f.read_bytes(),file_name=f.name,mime='text/csv')
