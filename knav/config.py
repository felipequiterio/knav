from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # KRPC
    krpc_address: str = "192.168.1.82"
    krpc_rpc_port: int = 50000
    krpc_stream_port: int = 50001
    krpc_name: str = "KNAV Flight Software"
    krpc_reconnect_max_wait: int = 30

    # GNC
    gnc_rate_hz: int = 20
    telemetry_broadcast_hz: int = 10

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Physics
    g0: float = 9.81

    # Gravity Turn Defaults
    gt_turn_start_alt: float = 1000.0
    gt_q_limit: float = 20000.0
    gt_q_throttle: float = 0.6
    gt_feather_80: float = 1.0
    gt_feather_95: float = 0.4
    gt_feather_98: float = 0.1
    gt_termination_apo_frac: float = 0.98
    gt_termination_q_max: float = 100.0

    # Node Executor
    ne_precision_throttle: float = 0.05
    ne_full_burn_threshold: float = 5.0
    ne_precision_threshold: float = 0.5
    ne_warp_margin: float = 5.0

    # Circularization
    circ_correction_threshold: float = 1.0
    circ_tolerance_frac: float = 0.02

    # Hohmann
    hohmann_phase_tolerance_deg: float = 1.0

    model_config = {"env_file": ".env"}
