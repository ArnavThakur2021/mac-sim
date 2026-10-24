# Presentation outline (11 slides)

1. **Title and question** — Why do wired and wireless MACs handle collisions differently? Speaker: introduce shared-medium contention.
2. **Layer 2 context** — Ethernet and Wi-Fi medium access; show protocol comparison table.
3. **CSMA/CD** — carrier sensing, collision detection, jam and backoff; point to `e1_throughput.png`.
4. **CSMA/CA DCF** — DIFS, randomized backoff, ACK, NAV; point to same sweep.
5. **Simulator design** — seeded slot loop and metric definitions; explain simplifications.
6. **Station scaling** — `e1_throughput.png` and `e1_collision_probability.png`; discuss contention trends.
7. **Load, CW and payload** — `load.csv`, `cw.csv`, `payload.csv`; explain queueing knee and overhead tradeoff.
8. **Hidden terminals** — `hidden.csv`; explain shared receiver and RTS/CTS reservation.
9. **Bianchi validation** — `e6_validation.png` and `validation.csv`; show point errors and caveats.
10. **Ethernet propagation** — `propagation.csv`; compare classic efficiency approximation with simulation.
11. **Conclusion and limitations** — summarize relative strengths, ideal channel assumptions, and future 802.11e/ax work.
