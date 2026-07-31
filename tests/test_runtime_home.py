from pathlib import Path


def test_runtime_files_live_outside_the_skill(sos_api):
    runtime_home = Path(sos_api.RUNTIME_HOME)

    assert runtime_home != sos_api.SKILL_ROOT
    assert sos_api.LOCAL_ENV_PATH == runtime_home / ".env.local"
    assert sos_api.CUIT_CATALOG_CACHE_PATH == runtime_home / ".cuit_catalog_cache.json"
    assert sos_api.CUIT_ALIASES_PATH == runtime_home / ".cuit_aliases.json"
    assert sos_api.DOCUMENT_CATALOG_CACHE_PATH == runtime_home / ".document_catalog_cache.json"
    assert sos_api.DRAFT_CACHE_DIR == runtime_home / ".draft_cache"
    assert sos_api.LOCAL_DATA_DIR == runtime_home / "local"


def test_explicit_runtime_home_is_expanded_and_resolved(sos_api, monkeypatch, tmp_path):
    configured = tmp_path / "custom-home"
    monkeypatch.setenv("SOS_CONTADOR_HOME", str(configured))

    assert sos_api.resolve_runtime_home() == configured.resolve()
