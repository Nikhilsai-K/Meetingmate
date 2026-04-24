from meetingmate.core.config import get_settings


def test_settings_loads_from_env() -> None:
    s = get_settings()
    assert s.database_url.startswith("postgresql")
    assert s.deepgram_api_key  # set in conftest
    assert s.rate_limit_free_meeting_hours_per_day >= 1
