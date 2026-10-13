from app.config.engine_config import load_engine_config


def test_engine_config_loads_with_version() -> None:
    cfg = load_engine_config()
    assert cfg.config_version == "1.2.0-iteration1-draft"


def test_engine_config_has_all_algorithm_sections() -> None:
    cfg = load_engine_config()
    for name in (
        "trust_estimation_alg1",
        "indirect_trust_alg2",
        "manipulation_detection_alg3",
        "decision_policy_alg4",
        "locality_a11",
    ):
        assert name in cfg.data
