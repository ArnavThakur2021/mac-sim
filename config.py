"""Central protocol defaults; times are seconds unless noted."""
from dataclasses import dataclass

@dataclass(frozen=True)
class CDConfig:
    rate_bps: float = 10_000_000
    slot_s: float = 51.2e-6
    ifg_s: float = 9.6e-6
    jam_bits: int = 32
    min_frame_bytes: int = 64
    max_frame_bytes: int = 1518
    payload_bits: int = 8184
    propagation_s: float = 5e-6
    retry_limit: int = 16
    max_backoff_stage: int = 10

@dataclass(frozen=True)
class CAConfig:
    rate_bps: float = 1_000_000
    payload_bits: int = 8184
    mac_header_bits: int = 272
    phy_header_bits: int = 128
    ack_bits: int = 112
    rts_bits: int = 160
    cts_bits: int = 112
    propagation_s: float = 1e-6
    slot_s: float = 50e-6
    sifs_s: float = 28e-6
    difs_s: float = 128e-6
    cw_min: int = 32  # number of backoff choices, 0..CW-1
    max_stage: int = 5
    retry_limit: int = 7

CD = CDConfig()
CA = CAConfig()
