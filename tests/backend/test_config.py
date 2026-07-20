from app.config import Settings


def test_shared_env_ignores_non_backend_settings(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_PORT=8080\nDEBUG=false\n", encoding="utf-8")

    settings = Settings(_env_file=env_file)

    assert settings.debug is False
    assert not hasattr(settings, "app_port")
