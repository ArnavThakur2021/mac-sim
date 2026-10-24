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
.block-container {max-width: 1460px; padding-top: 1.25rem;}
.hero {padding: 1.45rem 1.7rem; border-radius: 18px; background:linear-gradient(115deg,#101c32,#16415c 58%,#147d83); color:#f3f8fc; margin-bottom:1rem; box-shadow:0 8px 26px #10243a26;}
.hero h1 {margin:0 0 .35rem;color:white;font-size:2rem}.hero p {margin:0;color:#d0e5ed;font-size:1.02rem}
.phase-card {padding:1rem 1.15rem;border:1px solid #dce6ee;border-left:5px solid #0891b2;border-radius:12px;background:#f7fafc;margin:.8rem 0 1rem}
.phase-card h4 {margin:0 0 .35rem;color:#10243a}.phase-card p {margin:.2rem 0;color:#34465b}
.hint {color:#66788a;font-size:.9rem}
div[data-testid="stMetric"] {background:#f6f9fc;padding:.75rem;border:1px solid #e1e8ef;border-radius:12px}
</style>
<div class="hero"><h1>CSMA Interactive Lab</h1><p>Follow each station as it senses, waits, transmits, collides, backs off, or receives an ACK. Then compare the access methods.</p></div>
''',unsafe_allow_html=True)

COLORS={'idle':'#e8edf2','carrier sense':'#7dd3fc','backoff':'#fbbf24','DIFS wait':'#fde68a','success':'#34d399','collision':'#fb7185','frozen':'#c4b5fd'}

def status_color(status):
    lower=status.lower()
    for key,color in COLORS.items():
        if key.lower() in lower: return color
    return '#cbd5e1'

def draw_channel(event,n,protocol,step,total):
    """Draw the actual simulator event and every station's recorded state."""
    width=1120; height=430; left=54; right=width-54; bus_y=220
    xs=[left+(right-left)*(i+1)/(n+1) for i in range(n)]
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="width:100%;height:auto;background:#f8fbff;border:1px solid #d9e4ee;border-radius:18px">']
    parts.append('<defs><linearGradient id="head" x1="0" x2="1"><stop offset="0" stop-color="#10243a"/><stop offset="1" stop-color="#17616d"/></linearGradient><filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#10243a" flood-opacity=".16"/></filter></defs>')
    parts.append(f'<rect x="0" y="0" width="{width}" height="52" rx="18" fill="url(#head)"/>')
    parts.append(f'<text x="24" y="33" font-size="16" font-weight="700" fill="white">{escape(protocol)} · step {step+1} of {total}</text>')
    parts.append(f'<text x="{width-24}" y="33" text-anchor="end" font-size="13" fill="#d2e8ef">Simulated time {event["time_s"]:.6f} s</text>')
    parts.append(f'<line x1="48" y1="{bus_y}" x2="{width-48}" y2="{bus_y}" stroke="#334155" stroke-width="12" stroke-linecap="round"/>')
    parts.append(f'<line x1="{width-95}" y1="{bus_y}" x2="{width-58}" y2="{bus_y}" stroke="#334155" stroke-width="3" marker-end="url(#arrow)"/>')
    parts.append('<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#334155"/></marker></defs>')
    parts.append(f'<text x="{width/2}" y="{bus_y+42}" text-anchor="middle" font-size="13" font-weight="700" letter-spacing="1.5" fill="#52657a">SHARED MEDIUM</text>')
    involved=set(event.get('stations',[])); kind=event.get('kind','idle')
    if kind=='success' and involved:
        i=next(iter(involved)); x=xs[i]
        parts.append(f'<rect x="{x-53}" y="{bus_y-20}" width="106" height="40" rx="10" fill="#059669" filter="url(#shadow)"/>')
        parts.append(f'<text x="{x}" y="{bus_y-2}" text-anchor="middle" fill="white" font-size="12" font-weight="700">DATA FRAME</text><text x="{x}" y="{bus_y+13}" text-anchor="middle" fill="#d1fae5" font-size="10">ACK returned</text>')
        parts.append(f'<path d="M{x} {bus_y-28} C{x+65} {bus_y-85},{width-105} {bus_y-80},{width-75} {bus_y-32}" fill="none" stroke="#10b981" stroke-width="3" stroke-dasharray="7 6"/>')
    elif kind=='collision':
        for i in sorted(involved):
            x=xs[i]
            parts.append(f'<path d="M{x-13} {bus_y-25} l14 16 -11 0 14 25" stroke="#dc2626" stroke-width="5" fill="none"/>')
        parts.append(f'<rect x="{width/2-74}" y="{bus_y-52}" width="148" height="32" rx="16" fill="#fee2e2" stroke="#ef4444"/>')
        parts.append(f'<text x="{width/2}" y="{bus_y-31}" text-anchor="middle" fill="#b91c1c" font-size="14" font-weight="800">COLLISION</text>')
    for i,x in enumerate(xs):
        state=event.get('states',['idle']*n)[i]
        color=status_color(state)
        parts.append(f'<line x1="{x}" y1="150" x2="{x}" y2="{bus_y-9}" stroke="#94a3b8" stroke-width="2"/>')
        parts.append(f'<circle cx="{x}" cy="119" r="32" fill="{color}" stroke="#334155" stroke-width="2.5" filter="url(#shadow)"/>')
        parts.append(f'<text x="{x}" y="125" text-anchor="middle" font-size="15" font-weight="800" fill="#102033">S{i+1}</text>')
        short=escape(state[:21])
        parts.append(f'<text x="{x}" y="169" text-anchor="middle" font-size="11" font-weight="600" fill="#334155">{short}</text>')
        parts.append(f'<text x="{x}" y="192" text-anchor="middle" font-size="10" fill="#64748b">CW stage {event["stage"][i]}</text>')
        if i in involved and kind=='success':
            parts.append(f'<text x="{x}" y="77" text-anchor="middle" font-size="12" font-weight="800" fill="#047857">TRANSMIT</text>')
    legend=[('Waiting / idle','#e8edf2'),('Backoff','#fbbf24'),('Transmitting / success','#34d399'),('Collision','#fb7185'),('Frozen / busy','#c4b5fd')]
    start_x=38
    for label,color in legend:
        parts.append(f'<circle cx="{start_x+7}" cy="{height-31}" r="7" fill="{color}" stroke="#64748b"/>')
        parts.append(f'<text x="{start_x+20}" y="{height-27}" font-size="10" fill="#475569">{escape(label)}</text>')
        start_x+=min(220,85+len(label)*4)
    parts.append('</svg>')
    return ''.join(parts)

def explain_event(protocol,event):
    """Return a learner-facing explanation for this point in the trace."""
    kind=event['kind']
    if kind=='DIFS wait':
        return ('Wait for DIFS','Wi-Fi stations must first hear the channel idle for DIFS. This separates one exchange from the next before backoff resumes.')
    if kind=='backoff':
        return ('Backoff countdown','The channel was idle for one slot, so waiting stations reduce their counters by one. A counter freezes whenever the channel becomes busy.')
    if kind=='carrier sense':
        return ('Carrier sensing','Stations listen before transmitting. Stations with a positive backoff counter wait; when the channel is idle, their counters move toward zero.')
    if kind=='collision':
        if protocol=='CSMA/CD':
            return ('Collision detected','More than one station started together. Ethernet detects the collision while transmitting, sends a short jam signal, then chooses a larger random backoff window.')
        if protocol=='CSMA/CA':
            return ('No ACK: infer a collision','Wi-Fi cannot listen for a collision while sending. The sender treats a missing acknowledgement as failure, grows its contention window, and retries after a new random backoff.')
        return ('Overlapping transmissions','Several stations sent at once. This CSMA baseline has no collision detection, so the full frame airtime is wasted before the failed attempt is known.')
    if kind=='success':
        if protocol=='CSMA/CA':
            return ('Frame delivered','One station won the countdown. It sends the frame; the receiver waits SIFS and returns an ACK. With RTS/CTS enabled, the reservation exchange comes first.')
        return ('Frame delivered','One station acquired the medium and completed its frame. Other stations defer until the channel becomes idle again.')
    return ('Channel state',event.get('detail','The medium is being observed.'))

def sync_number_to_slider(number_key,slider_key,last):
    st.session_state[slider_key]=min(last,max(1,int(st.session_state[number_key])))

def sync_slider_to_number(number_key,slider_key,last):
    st.session_state[number_key]=min(last,max(1,int(st.session_state[slider_key])))

def move_event(number_key,slider_key,delta,last):
    value=min(last,max(1,int(st.session_state.get(slider_key,1))+delta))
    st.session_state[slider_key]=value
    st.session_state[number_key]=value

def reset_playback_clock(clock_key):
    st.session_state[clock_key]=time.monotonic()

@st.fragment(run_every=0.25)
def event_player(trace,n,protocol,delay,run_id):
    """Render controls under the diagram and advance continuously when enabled."""
    slider_key=f'trace_slider_{run_id}'; number_key=f'trace_number_{run_id}'
    auto_key=f'trace_auto_{run_id}'; clock_key=f'trace_clock_{run_id}'
    if slider_key not in st.session_state: st.session_state[slider_key]=1
    if number_key not in st.session_state: st.session_state[number_key]=1
    if auto_key not in st.session_state: st.session_state[auto_key]=False
    last=len(trace)
    if st.session_state[auto_key]:
        now=time.monotonic()
        previous=st.session_state.get(clock_key,now)
        if now-previous>=delay:
            current=int(st.session_state[slider_key])
            if current<last:
                st.session_state[slider_key]=current+1
                st.session_state[number_key]=current+1
                st.session_state[clock_key]=now
            else:
                st.session_state[auto_key]=False
    selected=min(last-1,max(0,int(st.session_state[slider_key])-1))
    event=trace[selected]
    st.markdown(draw_channel(event,n,protocol,selected,len(trace)),unsafe_allow_html=True)

    # Playback controls intentionally sit directly below the animated channel.
    col_auto,col_prev,col_next=st.columns([2,1,1])
    col_auto.toggle('Run animation continuously',key=auto_key,
                    on_change=reset_playback_clock,args=(clock_key,),
                    help='Automatically advance one recorded event at a time. Turn it off to pause.')
    col_prev.button('◀ Previous',disabled=selected==0,key=f'prev_{run_id}',
                    on_click=move_event,args=(number_key,slider_key,-1,last))
    col_next.button('Next ▶',disabled=selected>=last-1,key=f'next_{run_id}',
                    on_click=move_event,args=(number_key,slider_key,1,last))
    number_col,slider_col=st.columns([1,5])
    number_col.number_input('Event number',min_value=1,max_value=last,key=number_key,
                            on_change=sync_number_to_slider,args=(number_key,slider_key,last),
                            help='Type an event number to jump directly to it.')
    slider_col.slider('Event timeline',min_value=1,max_value=last,key=slider_key,
                      on_change=sync_slider_to_number,args=(number_key,slider_key,last),
                      help='Drag to inspect the recorded process. The default event is 1.')

    title,description=explain_event(protocol,event)
    st.markdown(f'<div class="phase-card"><h4>{escape(title)}</h4><p>{escape(description)}</p><p><b>Event detail:</b> {escape(event["detail"])}</p></div>',unsafe_allow_html=True)
    st.markdown('**Station states at this event**')
    rows=[{'Station':f'Station {i+1}','State now':state,
           'Backoff counter':event['backoff'][i],'Backoff stage':event['stage'][i]}
          for i,state in enumerate(event['states'])]
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)

def run_protocol(name,n,duration,seed,payload,rts):
    if name=='CSMA': return csma_simulate(n,duration,seed=seed,payload_bits=payload,record_trace=True)
    if name=='CSMA/CD': return cd_simulate(n,duration,seed=seed,payload_bits=payload,record_trace=True)
    return ca_simulate(n,duration,seed=seed,payload_bits=payload,rts_cts=rts,record_trace=True)

def metric_table(result):
    """Show five key outcomes with short, learner-friendly definitions."""
    rows=[
        ('Normalized throughput',f'{result["throughput"]:.3f}', 'Useful payload rate as a fraction of the configured link rate.'),
        ('Mean access delay',f'{result["mean_delay_s"]*1000:.3f} ms', 'Average time from a packet becoming ready until successful delivery.'),
        ('Collision probability',f'{result["collision_probability"]:.1%}', 'Collided transmission attempts divided by all transmission attempts.'),
        ('Frame drop rate',f'{result["drop_rate"]:.2%}', 'Retry-limit drops divided by counted attempts in this simulator.'),
        ("Jain's fairness",f'{result["fairness"]:.3f}', 'How evenly deliveries are shared: 1 means equal sharing.'),
    ]
    return pd.DataFrame(rows,columns=['Metric','Run value','What it tells you'])

# Setup controls are displayed in a full-width panel at the bottom of the page.
setup_defaults={'setup_stations':5,'setup_duration':0.12,'setup_payload':2048,
                'setup_seed':17,'setup_rts':False,'setup_delay':0.8}
for key,value in setup_defaults.items():
    if key not in st.session_state:
        st.session_state[key]=value
stations=st.session_state['setup_stations']
duration=st.session_state['setup_duration']
payload=st.session_state['setup_payload']
seed=st.session_state['setup_seed']
rts=st.session_state['setup_rts']
animation_delay=st.session_state['setup_delay']

lab,comparison,concepts=st.tabs(['▶ Working simulation','⇄ Compare protocols','Learn the terms'])
with lab:
    st.subheader('Watch stations use the channel')
    protocol=st.radio('Protocol to run',['CSMA','CSMA/CD','CSMA/CA'],horizontal=True)
    colrun,colhint=st.columns([1,3])
    with colrun:
        run_clicked=st.button('Run / reset simulation',type='primary',use_container_width=True)
    with colhint:
        st.markdown('<p class="hint">The animation shows events recorded by the simulator, rather than a prerecorded illustration.</p>',unsafe_allow_html=True)
    if run_clicked:
        result=run_protocol(protocol,stations,duration,int(seed),payload,rts)
        st.session_state['mac_result']=result
        st.session_state['mac_protocol']=protocol
        st.session_state['mac_run_id']=st.session_state.get('mac_run_id',0)+1
    result=st.session_state.get('mac_result')
    if result:
        trace=result.get('trace',[]); active_protocol=st.session_state.get('mac_protocol',protocol)
        if trace:
            run_id=st.session_state.get('mac_run_id',1)
            event_player(trace,stations,active_protocol,animation_delay,run_id)
            st.subheader('Metrics from the complete run')
            st.dataframe(metric_table(result),hide_index=True,use_container_width=True)
            st.caption(f"Trace contains the first {len(trace)} recorded events (maximum 300); metrics cover the full {result['elapsed_s']:.3f} s run · Seed: {int(seed)}")
    else:
        st.info('Choose a protocol and press **Run / reset simulation**. Then inspect each phase or play the trace at a slower pace.')

with comparison:
    st.subheader('Same scenario, three channel-access strategies')
    st.write('All three runs use the same station count, payload, duration, and random seed.')
    if st.button('Run comparative analysis',type='primary'):
        csma=csma_simulate(stations,duration,seed=int(seed),payload_bits=payload)
        cd=cd_simulate(stations,duration,seed=int(seed),payload_bits=payload)
        ca=ca_simulate(stations,duration,seed=int(seed),payload_bits=payload,rts_cts=rts)
        rows=[]
        for label,metrics in [('CSMA',csma),('CSMA/CD',cd),('CSMA/CA'+(' RTS/CTS' if rts else ' Basic'),ca)]:
            rows.append({'Protocol':label,'Normalized throughput':metrics['throughput'],
                         'Mean delay (ms)':metrics['mean_delay_s']*1000,
                         'Collision probability':metrics['collision_probability'],
                         'Frame drop rate':metrics['drop_rate'],"Jain's fairness":metrics['fairness']})
        st.session_state['mac_comparison']=pd.DataFrame(rows)
    comp=st.session_state.get('mac_comparison')
    if comp is not None:
        left,right=st.columns(2)
        with left:
            st.markdown('**Useful payload / configured link rate**')
            st.bar_chart(comp.set_index('Protocol')[['Normalized throughput']],horizontal=True)
        with right:
            st.markdown('**Transmission attempts that collided**')
            st.bar_chart(comp.set_index('Protocol')[['Collision probability']],horizontal=True)
        st.dataframe(comp.set_index('Protocol').style.format({'Normalized throughput':'{:.3f}','Mean delay (ms)':'{:.2f}','Collision probability':'{:.1%}','Frame drop rate':'{:.1%}',"Jain's fairness":'{:.3f}'}),use_container_width=True)
    else:
        st.info('Press **Run comparative analysis** to compare all three protocols with the current simulation settings below.')
    st.warning(f"CSMA/CD is configured at {CD.rate_bps/1e6:g} Mb/s; CSMA/CA at {CA.rate_bps/1e6:g} Mb/s. Throughput is normalized to each configured rate, so it compares channel efficiency rather than raw bit rate.")

with concepts:
    st.subheader('How does MAC access work?')
    st.markdown('''
**MAC** means *Media Access Control*. It is the part of the data-link layer that decides which station may use a shared channel and when. The problem is like several people sharing one walkie-talkie: listen first, take turns, and recover when two people speak together.

1. **Sense:** listen to see whether another station is using the medium.
2. **Wait:** if it is busy, defer. If it is idle, follow the protocol's inter-frame wait.
3. **Contend:** choose or resume a random backoff counter. Each idle slot reduces it; a busy channel freezes it.
4. **Transmit:** the station whose counter reaches zero sends its frame.
5. **Recover or confirm:** a collision causes backoff/retry; a successful Wi-Fi frame is confirmed by an ACK.
''')
    st.subheader('CSMA, CSMA/CD, and CSMA/CA')
    st.markdown('''
| Method | How it handles access | What happens after overlap |
|---|---|---|
| **CSMA** | Sense before sending; this project shows a baseline without collision detection. | The sender spends the full frame airtime before discovering failure. |
| **CSMA/CD** | Wired Ethernet senses, sends, and monitors the medium while transmitting. | Detects collision early, sends a jam signal, then uses binary exponential backoff. |
| **CSMA/CA** | Wi-Fi waits DIFS, uses randomized backoff, and freezes counters while busy. | It cannot reliably detect collision while transmitting; a missing ACK signals failure and the sender retries with a wider contention window. |
''')
    st.subheader('What are RTS and CTS?')
    st.markdown('''
**RTS** is *Request to Send*; **CTS** is *Clear to Send*. With RTS/CTS enabled, a Wi-Fi station first sends a short RTS. The access point replies with CTS, then the station sends its data and receives an ACK. Other stations that hear the CTS defer for the reserved time (the **Network Allocation Vector**, or NAV). This can help when two senders cannot hear each other but both reach the same access point: a CTS may warn the hidden sender to wait. The exchange adds overhead, so it can reduce efficiency for small frames and does not prevent every collision.
''')
    st.subheader('How to read the metrics')
    st.markdown('''
| Metric | Meaning | How to interpret it |
|---|---|---|
| **Normalized throughput** | Successfully delivered payload bits ÷ (simulation time × configured link rate). | A value of 0.70 means 70% of the configured rate carried useful payload in the model. |
| **Mean access delay** | Average wait from a packet becoming ready until successful delivery. | Lower is generally better; contention and retries tend to increase it. |
| **Collision probability** | Collided transmission attempts ÷ all transmission attempts. | Higher means stations more often transmit at the same time. |
| **Frame drop rate** | Retry-limit drops divided by counted attempts in this simulator. | Nonzero means some frames exceeded the retry limit. |
| **Jain's fairness** | `(sum of station deliveries)² ÷ (station count × sum of squared deliveries)`. | 1 means equal deliveries; near `1/N` means one station received nearly all deliveries. |
''')
    st.caption('The Bianchi curve below is an analytical saturation-throughput reference for CSMA/CA. It helps compare the DCF simulator with a mathematical model.')
    ns=list(range(2,51,2)); frame=pd.DataFrame([{'Stations':n,'Bianchi normalized throughput':solve(n)['throughput']} for n in ns])
    st.line_chart(frame.set_index('Stations'))
    with st.expander('Generated experiment figures'):
        for image in sorted((ROOT/'results/plots').glob('*.png')):
            st.image(str(image),caption=image.stem,use_container_width=True)

st.divider()
with st.container(border=True):
    st.header('Simulation setup')
    st.caption('Choose the scenario settings here, then run or reset a simulation above. The same seed reproduces the same random backoff choices.')
    setup_row1=st.columns(3)
    setup_row1[0].slider('Stations',2,12,key='setup_stations',help='Number of stations sharing the channel.')
    setup_row1[1].slider('Simulation duration (s)',0.03,0.5,step=0.01,key='setup_duration',help='A short horizon makes a quick visual run.')
    setup_row1[2].select_slider('Payload (bits)',options=[512,1024,2048,4096,8184],key='setup_payload')
    setup_row2=st.columns([1,1,2])
    setup_row2[0].number_input('Random seed',min_value=0,max_value=99999,key='setup_seed')
    setup_row2[1].toggle('Enable RTS/CTS in CSMA/CA',key='setup_rts')
    setup_row2[2].slider('Animation pause per event (seconds)',0.35,1.5,step=0.05,key='setup_delay',help='Longer pauses make each event easier to follow. Continuous playback can be paused at any time.')
