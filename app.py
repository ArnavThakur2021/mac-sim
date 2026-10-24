"""Animated, event-by-event MAC protocol simulator and comparison dashboard."""
from html import escape
from pathlib import Path
import sys
import time
import pandas as pd
import streamlit as st

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from config import CA, CD
from sim.csma import simulate as csma_simulate
from sim.csma_cd import simulate as cd_simulate
from sim.csma_ca import simulate as ca_simulate
from sim.bianchi import solve

st.set_page_config(page_title='CSMA Interactive Lab',page_icon='📡',layout='wide')
st.markdown('''
<style>
.block-container {max-width: 1450px; padding-top: 1.4rem;}
.hero {padding: 1.3rem 1.5rem; border-radius: 16px; background: linear-gradient(115deg,#10243a,#163b55); color:#f3f8fc; margin-bottom:1rem;}
.hero h1 {margin:0 0 .35rem 0; color:white;} .hero p {margin:0;color:#c5d9e7;}
.event-card {padding: .8rem 1rem; border-radius: 10px; background:#f3f6fa; border-left:5px solid #27a5a0; margin:.5rem 0;}
.small-note {color:#65758b;font-size:.9rem;}
</style>
<div class="hero"><h1>CSMA Interactive Lab</h1><p>Watch stations sense, contend, transmit, collide, back off, and acknowledge frames. Then compare the three access methods.</p></div>
''',unsafe_allow_html=True)

COLORS={'idle':'#e8edf2','carrier sense':'#93c5fd','backoff':'#fbbf24','DIFS wait':'#fde68a','success':'#34d399','collision':'#fb7185','frozen':'#c4b5fd'}

def status_color(status):
    lower=status.lower()
    for key,color in COLORS.items():
        if key.lower() in lower: return color
    return '#cbd5e1'

def draw_channel(event,n,protocol,step,total):
    """Build a small SVG of the current, actual simulator event."""
    width=1040; height=350; left=58; right=width-58; bus_y=178
    xs=[left+(right-left)*(i+1)/(n+1) for i in range(n)]
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="width:100%;height:auto;background:#fbfdff;border:1px solid #d9e2ec;border-radius:14px">']
    parts.append(f'<text x="28" y="30" font-size="15" font-weight="700" fill="#334155">{escape(protocol)} · event {step+1}/{total}</text>')
    parts.append(f'<line x1="48" y1="{bus_y}" x2="{width-48}" y2="{bus_y}" stroke="#475569" stroke-width="8" stroke-linecap="round"/>')
    parts.append(f'<text x="{width/2}" y="{bus_y+33}" text-anchor="middle" font-size="14" fill="#475569">SHARED CHANNEL</text>')
    involved=set(event.get('stations',[])); kind=event.get('kind','idle')
    if kind=='success' and involved:
        i=next(iter(involved)); x=xs[i]
        parts.append(f'<rect x="{x-44}" y="{bus_y-16}" width="88" height="32" rx="8" fill="#059669"/><text x="{x}" y="{bus_y+5}" text-anchor="middle" fill="white" font-size="12" font-weight="700">DATA / ACK</text>')
    elif kind=='collision':
        for i in sorted(involved):
            x=xs[i]
            parts.append(f'<path d="M{x-12} {bus_y-18} l12 14 -10 0 13 21" stroke="#dc2626" stroke-width="5" fill="none"/>')
        parts.append(f'<text x="{width/2}" y="{bus_y-28}" text-anchor="middle" fill="#b91c1c" font-size="14" font-weight="700">COLLISION</text>')
    for i,x in enumerate(xs):
        state=event.get('states',['idle']*n)[i]
        color=status_color(state)
        parts.append(f'<line x1="{x}" y1="98" x2="{x}" y2="{bus_y-7}" stroke="#94a3b8" stroke-width="2"/>')
        parts.append(f'<circle cx="{x}" cy="72" r="25" fill="{color}" stroke="#334155" stroke-width="2"/>')
        parts.append(f'<text x="{x}" y="77" text-anchor="middle" font-size="13" font-weight="700" fill="#102033">S{i+1}</text>')
        short=escape(state[:19])
        parts.append(f'<text x="{x}" y="113" text-anchor="middle" font-size="10" fill="#334155">{short}</text>')
        if i in involved and kind=='success':
            parts.append(f'<text x="{x}" y="47" text-anchor="middle" font-size="12" fill="#047857">TX</text>')
    if kind=='collision':
        parts.append(f'<text x="{width/2}" y="{height-35}" text-anchor="middle" font-size="12" fill="#991b1b">{escape(event.get("detail", "Overlapping transmissions"))}</text>')
    elif kind=='success':
        parts.append(f'<text x="{width/2}" y="{height-35}" text-anchor="middle" font-size="12" fill="#047857">{escape(event.get("detail", "Frame delivered"))}</text>')
    else:
        parts.append(f'<text x="{width/2}" y="{height-35}" text-anchor="middle" font-size="12" fill="#475569">{escape(event.get("detail", kind))}</text>')
    parts.append('</svg>')
    return ''.join(parts)

def run_protocol(name,n,duration,seed,payload,rts):
    if name=='CSMA': return csma_simulate(n,duration,seed=seed,payload_bits=payload,record_trace=True)
    if name=='CSMA/CD': return cd_simulate(n,duration,seed=seed,payload_bits=payload,record_trace=True)
    return ca_simulate(n,duration,seed=seed,payload_bits=payload,rts_cts=rts,record_trace=True)

with st.sidebar:
    st.header('Simulation setup')
    stations=st.slider('Stations',2,12,5,help='Number of stations sharing the channel.')
    duration=st.slider('Simulation duration (s)',0.03,0.5,0.12,0.01,help='Keep short for a quick visual run.')
    payload=st.select_slider('Payload (bits)',options=[512,1024,2048,4096,8184],value=2048)
    seed=st.number_input('Random seed',min_value=0,max_value=99999,value=17)
    rts=st.toggle('Enable RTS/CTS in CSMA/CA',value=False)
    st.caption('A fixed seed gives repeatable backoff choices.')

lab,comparison,concepts=st.tabs(['▶ Working simulation','⇄ Compare protocols','How MAC access works'])
with lab:
    st.subheader('Watch the channel state change')
    protocol=st.radio('Protocol to run',['CSMA','CSMA/CD','CSMA/CA'],horizontal=True)
    colrun,colhint=st.columns([1,3])
    with colrun:
        run_clicked=st.button('Run / reset simulation',type='primary',use_container_width=True)
    with colhint:
        st.markdown('<p class="small-note">The trace below comes from the same seeded simulator used to calculate the metrics.</p>',unsafe_allow_html=True)
    if run_clicked:
        result=run_protocol(protocol,stations,duration,int(seed),payload,rts)
        st.session_state['mac_result']=result
        st.session_state['mac_protocol']=protocol
        st.session_state['mac_step']=0
        st.session_state['mac_run_id']=st.session_state.get('mac_run_id',0)+1
    result=st.session_state.get('mac_result')
    if result:
        trace=result.get('trace',[]); active_protocol=st.session_state.get('mac_protocol',protocol)
        if trace:
            run_id=st.session_state.get('mac_run_id',1)
            step_key=f'trace_step_{run_id}'
            selected=min(st.session_state.get(step_key,st.session_state.get('mac_step',0)),len(trace)-1)
            if st.session_state.get('previous_event',False):
                st.session_state[step_key]=max(0,selected-1)
            if st.session_state.get('next_event',False):
                st.session_state[step_key]=min(len(trace)-1,selected+1)
            if st.session_state.get('play_events',False):
                end=min(len(trace),selected+13)
                area=st.empty()
                for idx in range(selected,end):
                    area.markdown(draw_channel(trace[idx],stations,active_protocol,idx,len(trace)),unsafe_allow_html=True)
                    time.sleep(0.25)
                st.session_state[step_key]=max(selected,end-1)
            step=st.slider('Step through events',0,len(trace)-1,selected,key=step_key,help='Move through DIFS, backoff, data, collisions, and ACK events.')
            st.session_state['mac_step']=step
            event=trace[step]
            st.markdown(draw_channel(event,stations,active_protocol,step,len(trace)),unsafe_allow_html=True)
            bar1,bar2,bar3=st.columns([1,1,3])
            with bar1:
                st.button('◀ Previous',disabled=step==0,key='previous_event')
            with bar2:
                st.button('Next ▶',disabled=step>=len(trace)-1,key='next_event')
            with bar3:
                st.button('▶ Play next 12 events',key='play_events')
            st.markdown(f'<div class="event-card"><b>t = {event["time_s"]:.6f} s · {escape(event["kind"].upper())}</b><br>{escape(event["detail"])}</div>',unsafe_allow_html=True)
            station_rows=[]
            for i,state in enumerate(event['states']):
                station_rows.append({'Station':f'Station {i+1}','Current state':state,
                                     'Backoff counter':event['backoff'][i],
                                     'Backoff stage':event['stage'][i]})
            st.dataframe(pd.DataFrame(station_rows),hide_index=True,use_container_width=True)
        st.divider(); st.subheader('Metrics from this run')
        cols=st.columns(4)
        for col,label,key,fmt in [(cols[0],'Normalized throughput','throughput','{:.3f}'),(cols[1],'Mean access delay','mean_delay_s','{:.4f} s'),(cols[2],'Collision probability','collision_probability','{:.1%}'),(cols[3],"Jain's fairness",'fairness','{:.3f}')]:
            col.metric(label,fmt.format(result[key]))
        st.caption(f"{result['attempts']} attempts · {result['collisions']} collided attempts · {result['drops']} drops. Trace is capped at {len(trace)} events.")
    else:
        st.info('Choose a protocol, then press **Run / reset simulation** to create a trace. Use the event slider or Play button to watch it unfold.')

with comparison:
    st.subheader('Same scenario, three channel-access strategies')
    st.write('Run CSMA without collision detection, CSMA/CD, and CSMA/CA with the same station count, payload, duration, and random seed.')
    if st.button('Run comparative analysis',type='primary'):
        csma=csma_simulate(stations,duration,seed=int(seed),payload_bits=payload)
        cd=cd_simulate(stations,duration,seed=int(seed),payload_bits=payload)
        ca=ca_simulate(stations,duration,seed=int(seed),payload_bits=payload,rts_cts=rts)
        rows=[]
        for label,metrics in [('CSMA',csma),('CSMA/CD',cd),('CSMA/CA'+(' RTS/CTS' if rts else ' Basic'),ca)]:
            rows.append({'Protocol':label,'Normalized throughput':metrics['throughput'],
                         'Mean delay (ms)':metrics['mean_delay_s']*1000,
                         'Collision probability':metrics['collision_probability'],
                         'Drop rate':metrics['drop_rate'],"Jain's fairness":metrics['fairness']})
        st.session_state['mac_comparison']=pd.DataFrame(rows)
    comp=st.session_state.get('mac_comparison')
    if comp is not None:
        left,right=st.columns(2)
        with left:
            st.markdown('**Useful payload delivered**')
            st.bar_chart(comp.set_index('Protocol')[['Normalized throughput']],horizontal=True)
        with right:
            st.markdown('**Attempts ending in collision**')
            st.bar_chart(comp.set_index('Protocol')[['Collision probability']],horizontal=True)
        st.dataframe(comp.set_index('Protocol').style.format({'Normalized throughput':'{:.3f}','Mean delay (ms)':'{:.2f}','Collision probability':'{:.1%}','Drop rate':'{:.1%}',"Jain's fairness":'{:.3f}'}),use_container_width=True)
    else:
        st.info('Press **Run comparative analysis** to compare all three protocols under the current settings.')
    st.warning(f"The CD/CSMA link rate is {CD.rate_bps/1e6:g} Mb/s and the CA rate is {CA.rate_bps/1e6:g} Mb/s. Throughput is normalized to each configured link rate, so compare protocol behavior and overhead rather than raw bit rates.")

with concepts:
    st.subheader('What you should see')
    st.markdown('''
| Method | What stations do | If attempts overlap |
|---|---|---|
| **CSMA** | Sense the shared channel before sending. | A frame may be lost; the sender only learns after the frame interval. |
| **CSMA/CD** | Sense, send, and monitor the wired medium while transmitting. | Detects the collision, sends a jam signal, then applies binary exponential backoff. |
| **CSMA/CA** | Wait DIFS, count down a random backoff, and freeze the counter while busy. | No collision detection; a missing ACK indicates failure, so the contention window grows. RTS/CTS can reserve the channel. |

Use **Run / reset simulation** and the event slider to pause on each phase. The colored station circles show each station's current state; the event card describes what just happened. **Play next 12 events** animates the trace.
''')
    st.subheader('Compare against the saturation model')
    ns=list(range(2,51,2)); frame=pd.DataFrame([{'Stations':n,'Bianchi throughput':solve(n)['throughput']} for n in ns])
    st.line_chart(frame.set_index('Stations'))
    st.caption('Bianchi curve is the analytical saturation-throughput reference for CSMA/CA. The live comparison above uses the discrete-event simulator.')
    with st.expander('Open generated experiment figures'):
        for image in sorted((ROOT/'results/plots').glob('*.png')):
            st.image(str(image),caption=image.stem,use_container_width=True)
