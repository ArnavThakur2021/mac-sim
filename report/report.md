# CSMA/CA Performance Analysis in Wireless Networks and Comparative Analysis of CSMA/CD and CSMA/CA

## Abstract

This project implements educational slot-based models of Ethernet CSMA/CD and 802.11-style DCF CSMA/CA, a fixed-point saturation-throughput calculation, a hidden-terminal experiment, parameter sweeps, and a Streamlit demonstration. The code is deterministic for a fixed seed. On the recorded fast validation run, the basic and RTS/CTS simulation points had a mean absolute percentage error of 3.49% against the implemented Bianchi model over even station counts 2–50. At 10 saturated stations, the analytical basic-access throughput is 0.7579 and the simulated value is 0.7366; RTS/CTS analytical/simulation are 0.8370/0.8200. Generated outputs and exact inputs are in `results/data/` and `results/plots/`. These are educational approximations, not a standards conformance test.

## 1. Introduction and motivation

A MAC protocol coordinates access to a shared channel. A station must decide when to transmit, how to respond to overlapping transmissions, and how to share capacity with other stations. Ethernet and Wi-Fi solve this under different physical constraints. Traditional half-duplex Ethernet can detect a collision while transmitting. A Wi-Fi radio generally cannot reliably distinguish its own strong transmission from another station's signal, so it uses collision avoidance and receiver acknowledgements.

The central questions are how throughput, delay, collisions, and fairness change with the number of contending stations, offered load, payload size, and contention-window settings, and what RTS/CTS contributes when stations cannot sense one another.

## 2. Background

### 2.1 ALOHA and carrier sensing

Pure ALOHA allows transmission at any time, so frames overlap freely. Slotted ALOHA restricts starts to slot boundaries and reduces the vulnerable interval. CSMA improves this by sensing the medium first. Carrier sensing cannot eliminate collisions because propagation delay means two stations can each observe an idle channel before hearing the other.

### 2.2 CSMA/CD

Classic shared Ethernet uses 1-persistent carrier sensing: transmit when idle, detect a collision during transmission, send a jam sequence, and retry after binary exponential backoff. For the k-th collision the random delay is selected from an exponentially growing slot range, capped at 10 stages; a frame is abandoned after the retry limit. Modern switched full-duplex Ethernet does not normally encounter this shared-medium collision process, so this project models classic half-duplex Ethernet for teaching.

### 2.3 CSMA/CA and DCF

IEEE 802.11 DCF senses the channel, waits for DIFS, and chooses a random counter. The counter decreases on idle slots and freezes while the medium is busy. A successful data frame is followed by SIFS and ACK; without an ACK, the sender infers loss and expands its contention window. RTS/CTS optionally reserves airtime before a long data frame. Stations that hear reservation control frames can set a Network Allocation Vector (NAV), a virtual carrier-sense timer.

### 2.4 Hidden and exposed terminals

Hidden senders are outside one another's sensing range but can both reach a receiver, so they may overlap at that receiver. CTS can inform a hidden sender of an ongoing reservation. The exposed-terminal case is the reverse inefficiency: a station hears a nearby transmission and defers even though a simultaneous transmission to a different receiver could have succeeded.

## 3. Why collision detection does not transfer to wireless

A wireless transmitter's own signal is far stronger at its antenna than a remote station's signal. While transmitting, a commodity half-duplex radio cannot reliably receive and compare the channel to its transmitted waveform. Propagation, fading, and the near-far problem add uncertainty. Wi-Fi therefore relies on carrier sensing, randomized contention, ACK timeouts and optional reservation. RTS/CTS reduces the cost of some collisions; it does not make collisions impossible.

## 4. System model and assumptions

The constants are centralized in `config.py`. Important defaults are summarized below.

| Parameter | CSMA/CD | CSMA/CA |
|---|---:|---:|
| Nominal rate | 10 Mb/s | 1 Mb/s |
| Slot | 51.2 µs | 50 µs |
| Inter-frame spacing | 9.6 µs IFG | DIFS 128 µs; SIFS 28 µs |
| Payload default | 8184 bits | 8184 bits |
| Propagation | 5 µs | 1 µs |
| Retry/backoff cap | 16 attempts; stage 10 | 7 retries; stage 5 |
| Initial window | binary exponential | 32 choices |

Time is represented by continuous seconds advanced in discrete idle slots or protocol busy intervals. The CA model implements saturated stations and Bernoulli-per-slot arrival approximations for the offered-load experiment. The CD model uses one-frame queues. The simulator assumes an ideal channel and equal-rate stations. Metrics are defined in `sim/common.py`; throughput is useful payload bits divided by elapsed time and link rate, collision probability is collided attempts over total attempts, and Jain's index is computed from per-station delivery counts.

## 5. Simulator design

### 5.1 CSMA/CD event loop

1. Generate arrivals if using non-saturated mode.
2. Collect stations with queued data and zero backoff.
3. One ready station succeeds; multiple ready stations collide and independently draw a new backoff.
4. If none is ready, advance an idle slot and decrement positive counters.

The collision busy interval includes propagation detection and the jam signal. The successful busy interval includes the frame and IFG.

### 5.2 CSMA/CA event loop

1. Advance idle time until DIFS has elapsed.
2. Decrement all active backoff counters on idle slots.
3. Freeze counters during data/control busy intervals.
4. One zero-counter station receives success and resets its stage; simultaneous zero counters collide, expand the stage and draw a new counter.
5. Add protocol busy duration and require another idle DIFS before counter progress resumes.

The duration helper supplies success, collision and slot times to both the simulator and Bianchi calculation. RTS/CTS changes these durations. The current state loop is intentionally compact and omits many frame-level timers and receiver-specific NAV behavior.

### 5.3 Shared metric calculation

Both simulators return the same metric keys: normalized throughput, mean and 95th percentile access delay, collision probability, drop rate, success/collision/idle fractions, fairness, per-station deliveries and throughput, elapsed time, attempts, collisions, and drops. The dashboard displays a subset; experiment CSVs preserve all scalar outputs plus station vectors.

## 6. Analytical models

### 6.1 Bianchi saturation model

The implementation solves the fixed point in attempt probability τ and conditional collision probability p:

`τ = 2(1-2p) / ((1-2p)(W+1) + pW(1-(2p)^m))`

`p = 1 - (1-τ)^(n-1)`

It then computes the probabilities of an idle slot, a successful busy slot, and a collision busy slot. Throughput divides the expected successfully delivered payload in a renewal slot by the expected duration of that slot. The root is found numerically with a bracketed solver. Results in `validation.csv` use the configured timing assumptions and should be interpreted as model-to-model validation rather than validation against a radio trace.

### 6.2 Ethernet efficiency approximation

The classic approximation is `η = 1/(1+6.44a)`, where `a` is propagation time divided by frame transmission time. It predicts declining efficiency as propagation consumes more of a frame's transmission interval. The E7 file records this formula beside the simulated points.

## 7. Experiments and results

All tables and charts below derive from the checked-in CSV/PNG outputs. The final included run was `python experiments/run_all.py` without `--fast`: five seeds for the main sweeps, 1 simulated second for saturated sweep points, 0.5 seconds for Poisson load points, and a fixed 5 second run per Bianchi point. These horizons remain compact compared with production studies, so present them as educational trends and not precise deployment predictions. Since the model is stochastic, regenerate before presenting and report the selected run mode.

### E1. Number of stations

See `e1_combined.png`, the four per-metric E1 plots, and `stations.csv`. Across five seeds, basic CA throughput at N=2, 10, and 50 is 0.8331, 0.7382, and 0.4223. RTS/CTS is 0.8086, 0.8249, and 0.7955 at those same points. Collision probability increases from about 0.06 at N=2 to 0.74 basic-access at N=50. RTS/CTS's throughput advantage at higher N is specific to the configured long payload and modeled airtime costs. CD throughput appears near 0.98, but fairness drops from 0.5 at N=2 to 0.02 at N=50 because the simplified model lets a successful saturated station restart immediately; this is a known unfairness artifact, not a general property of Ethernet.

### E2. Offered load

`load.csv`, `e2_throughput.png`, and `e2_mean_delay_s.png` sweep 0.1–1.5 of nominal capacity at N=10 and 30. Arrival rates are derived from payload bit rate per station. As offered load approaches service capacity, queue delay and delivered throughput should diverge from the low-load linear regime. This experiment's Poisson input is approximated by Bernoulli arrivals at slot checks; the plotted points are short-run demonstrations, not precise queueing estimates.

### E3. Contention window

`cw.csv` and `e3_cw.png` sweep CWmin 8–128 at N=10 and 40. A narrow window makes repeated simultaneous attempts more likely; a wide window reduces collision probability but spends more time in idle countdown. Because this fast sweep averages two brief seeded samples, it is best used to demonstrate tradeoff direction rather than choose an optimal production CW.

### E4. Payload size

`payload.csv` and `e4_payload.png` sweep payload 256–12000 bits. The five-seed averages show basic access ahead through 2048 bits (0.5595 vs 0.5345 at 2048), while RTS/CTS is ahead at 4096 bits (0.6963 vs 0.6627); the observed crossover is between 2048 and 4096 bits. This crossover depends on the configured timing model, payload, and station count and should not be generalized to every WLAN.

### E5. Hidden terminals

`hidden.csv` and `e5_hidden.png` compare collision cost across hidden sender-pair counts. At 10 pairs, mean collision probability is 0.446 basic and 0.429 with RTS/CTS, while collision airtime fraction falls from 0.258 to 0.015. This illustrates RTS/CTS's primary benefit in this model: collisions waste a short RTS interval rather than a long data frame. Topology and NAV are simplified: no detailed per-node control-frame event trace is modeled, so this result supports the airtime-cost lesson, not a quantitative 802.11 prediction.

### E6. Bianchi validation

`validation.csv` and `e6_validation.png` compare both basic and RTS/CTS modes for even N=2–50. The recorded run's overall mean absolute percentage error is **3.49%**. For basic access at N=10, analytical throughput is **0.7579** and simulated throughput is **0.7366** (2.81% relative error). For RTS/CTS at N=10, the values are **0.8370** and **0.8200** (2.03%). Basic mode's maximum point error is 9.18% at N=50, while RTS/CTS's maximum is about 2.98%. That means the overall trend matches closely under the configured long validation duration, but not every point is within 5%.

### E7. Propagation delay and Ethernet

`propagation.csv` and `e7_propagation.png` plot 1–50 µs. The classic approximation decreases from 0.9923 at 1 µs to 0.7192 at 50 µs. Simulated CD normalized throughput stays at 0.9804 across this particular saturated sweep. This discrepancy is informative: the model only charges propagation on the collision interval and does not model collision probability as a full bandwidth-delay window, so it cannot reproduce the classic efficiency law. It is a known model limitation rather than evidence that propagation has no effect.

## 8. Comparative analysis

| Dimension | CSMA/CD | CSMA/CA |
|---|---|---|
| Typical medium | Classic shared wired Ethernet | Wireless LAN |
| Medium observation | Electrical carrier sensing | Physical and virtual carrier sensing |
| Collision handling | Detect while transmitting; jam and abort | Infer failure from missing ACK/timeout |
| Access policy | 1-persistent in this model | DCF contention window |
| Backoff | Binary exponential slots | Random slots with freeze/resume |
| ACK | Not used by classic Ethernet MAC | Link ACK is central to delivery confirmation |
| Reservation | None | Optional RTS/CTS and NAV |
| Hidden nodes | Generally not the characteristic issue on a shared cable | Can cause collisions at receiver |
| Fixed overhead | IFG and collision jam | DIFS/SIFS, ACK and optional RTS/CTS |
| Long propagation | Enlarges collision vulnerability | Adds response/timeout cost |
| Fairness | Depends on contention dynamics; model is short-run unfair | Random backoff tends toward sharing but finite samples vary |
| Modern context | Switched full-duplex Ethernet largely removes collisions | Still fundamental Wi-Fi access method, with later QoS/PHY extensions |

## 9. Limitations and future work

The model is slotted and omits complete PHY preambles, real ACK timeouts, capture effect, fading, hidden-node-specific packet overlap timelines, rate adaptation, and detailed per-node NAV expiry. The CA arrival process uses slot-sampled Bernoulli arrivals, and the CD model's backoff approximation can make fairness unrepresentative. Experiments in fast mode are intentionally short. The dashboard timeline visualizer and animated event stepping are not implemented, and the dashboard does not expose every requested control. RTS/CTS validation aligns with the analytical helper but should not be read as independent empirical verification.

Future work includes a true event queue with per-receiver overlap checks, complete NAV state, confidence intervals and longer runs by default, EDCA/QoS queues, capture and fading, 802.11ax/OFDMA abstractions, and cross-validation against ns-3 or trace data.

## 10. Conclusion

The project makes the collision-detection versus collision-avoidance distinction executable and inspectable. Bianchi's model provides a useful saturation trend check: the recorded aggregate error is 3.49% across two access modes and 25 even-N points. The sweeps expose how station count, payload, backoff window, and hidden senders affect channel use, while also showing why careful model accounting matters. The largest deviations are documented rather than hidden: short runs are noisy, the Ethernet model does not fully capture bandwidth-delay efficiency, and the hidden-terminal model is deliberately compact.

## 11. References

1. G. Bianchi, “Performance Analysis of the IEEE 802.11 Distributed Coordination Function,” *IEEE Journal on Selected Areas in Communications*, vol. 18, no. 3, pp. 535–547, 2000.
2. IEEE Std 802.11, Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications.
3. IEEE Std 802.3, Ethernet.
4. J. F. Kurose and K. W. Ross, *Computer Networking: A Top-Down Approach*, Pearson.
5. A. S. Tanenbaum and D. J. Wetherall, *Computer Networks*, Pearson.
6. R. M. Metcalfe and D. R. Boggs, “Ethernet: Distributed Packet Switching for Local Computer Networks,” *Communications of the ACM*, vol. 19, no. 7, pp. 395–404, 1976.
