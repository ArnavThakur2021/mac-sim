# CSMA/CA Performance Analysis in Wireless Networks

A small, explainable Python simulator comparing wired CSMA/CD with 802.11-style CSMA/CA, including a Bianchi saturation model and an interactive Streamlit dashboard.

## Run it

Python 3.10+ is required. From this directory:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
python experiments/run_all.py --fast
streamlit run app.py
```

The fast sweep generates CSV/PNG outputs in `results/`; omit `--fast` for five random seeds and longer runs. `run.sh` performs setup, tests, a fast sweep and starts Streamlit. On Windows use `run.bat`.

## Layout

`config.py` contains defaults; `sim/` contains the protocol and analytical models; `experiments/` contains sweep entry points; `tests/` holds unit tests; `results/data/` and `results/plots/` store generated outputs; `report/` has the written discussion and presentation material.

The dashboard opens as a working simulation lab. Choose CSMA, CSMA/CD, or CSMA/CA, run a seeded scenario, then use the event slider, Previous/Next controls, or **Play next 12 events** to watch channel sensing, DIFS, backoff, transmission, collisions, and ACK behavior unfold station by station. The comparison tab runs the three protocols with the same station count, payload, duration, and seed, then charts normalized throughput and collision probability alongside delay and fairness. Dashboard runs are intentionally short for responsiveness.

## Assumptions

This is an educational slotted approximation. It does not model RF capture, fading, rate adaptation, or full IEEE state machines. See the report for model boundaries and known deviations. Re-run experiments before quoting numerical values.
