# Viva notes

## Questions and short answers
1. **Why use CSMA?** It lets stations check a shared medium before transmitting.
2. **What is persistence?** The rule for what a station does when the channel is busy or idle.
3. **Why does Ethernet detect collisions?** A wired interface can monitor the medium while sending.
4. **Why is Wi-Fi collision detection difficult?** Its own transmit power overwhelms the received signal and it cannot reliably hear a collision.
5. **Why does CW grow after collision?** A larger random window lowers the chance of repeated synchronized attempts.
6. **What is binary exponential backoff?** Doubling the contention window after each failed attempt up to a cap.
7. **What is DIFS?** The idle interval before DCF contention resumes.
8. **What is SIFS?** A shorter interval used for immediate responses such as ACK and CTS.
9. **What does an ACK establish?** The sender received confirmation that its frame arrived.
10. **What is RTS/CTS?** A short reservation handshake before sending a data frame.
11. **What is NAV?** A virtual carrier-sense timer that defers stations for a reserved exchange.
12. **What is a hidden terminal?** Two senders cannot sense each other but collide at a common receiver.
13. **How can RTS/CTS help?** The receiver's CTS can be heard by a hidden sender and reserve the medium.
14. **What is an exposed terminal?** A station defers after hearing a nearby transmission even though its own receiver could be reached concurrently.
15. **What does saturation mean?** Each station always has a frame waiting.
16. **What does offered load mean?** The rate at which new frames arrive to queues.
17. **Why use a seeded generator?** It makes runs repeatable for debugging and comparison.
18. **What is normalized throughput?** Delivered payload divided by elapsed time and channel rate.
19. **What does Jain's index measure?** How evenly successful packets are distributed among stations.
20. **What does Bianchi model?** Saturated DCF attempt probability and collision probability as a fixed point.
21. **What assumptions affect Bianchi accuracy?** Ideal channel, homogeneous saturated stations, and independent attempts.
22. **What happens as station count rises?** More contention generally raises collision probability and decreases per-station opportunity.
23. **Why does RTS/CTS hurt small packets?** Its handshake consumes extra airtime relative to payload.
24. **What is the retry limit?** The maximum number of failed attempts before a frame is dropped.
25. **What is a limitation of this simulator?** Its event model is slotted and omits detailed PHY behavior.
26. **Why compare CD and CA carefully?** They target different media and use different PHY rates and overheads.
27. **What is a confidence interval?** An estimated range expressing uncertainty in a sample mean.
28. **Why include payload size sweeps?** Control overhead matters less as payload duration grows.

## Source file guide
- `config.py`: protocol constants.
- `sim/common.py`: station state and shared metrics.
- `sim/csma_cd.py`: wired collision-detection/backoff model.
- `sim/csma_ca.py`: wireless DCF/backoff model.
- `sim/bianchi.py`: analytical fixed point.
- `sim/hidden_terminal.py`: carrier-sense graph and shared-receiver experiment.
- `experiments/run_all.py`: reproducible sweep and plotting entry point.
- `app.py`: Streamlit interface.
- `tests/`: behavior and reproducibility checks.
