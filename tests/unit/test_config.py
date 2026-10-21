from pathlib import Path

import pytest
import yaml

from nostradamus_research.config import ConfigError, ProviderConfig, load_config, load_providers


def test_repository_config_loads(cfg):
    assert cfg.project.project.milestone == "M1"
    assert sum(cfg.corpus.targets.full_corpus.values()) == 80
    assert sum(cfg.corpus.targets.pilot.values()) == 20
    assert cfg.corpus.splits.targets == {"development": 48, "validation": 12, "test": 20}
    assert set(cfg.translation.pipelines) == {
        "A_direct",
        "B_two_stage",
        "C_retrieval",
        "D_structured",
    }


def test_unknown_key_is_rejected(tmp_path: Path, repo_root: Path):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    for name in ("project", "corpus", "translation", "evaluation"):
        (cfg_dir / f"{name}.yaml").write_text(
            (repo_root / "config" / f"{name}.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
    data = yaml.safe_load((cfg_dir / "corpus.yaml").read_text(encoding="utf-8"))
    data["splits"]["sede"] = 1  # typo
    (cfg_dir / "corpus.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ConfigError, match="sede"):
        load_config(tmp_path)


def test_missing_file_is_reported(tmp_path: Path):
    (tmp_path / "config").mkdir()
    with pytest.raises(ConfigError, match="missing configuration file"):
        load_config(tmp_path)


def test_example_providers_disable_paid_calls(repo_root: Path):
    providers = load_providers(repo_root, repo_root / "config" / "providers.example.yaml")
    assert providers.providers["mock"].type == "mock"
    for name in ("anthropic", "openai"):
        p = providers.providers[name]
        assert p.enabled is False
        assert p.api_key_env and p.api_key_env.endswith("_API_KEY")
    assert providers.logging.log_prompts is False


def test_paid_provider_requires_key_env():
    with pytest.raises(ValueError, match="api_key_env"):
        ProviderConfig(type="anthropic", model="x")
