import re

with open("tests/agent/test_auxiliary_client.py", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """    def test_ttl_expiry_evicts(self):
        from agent.auxiliary_client import (
            _mark_provider_unhealthy,
            _is_provider_unhealthy,
            _aux_unhealthy_until,
        )
        _mark_provider_unhealthy("openrouter", ttl=0.01)
        assert _is_provider_unhealthy("openrouter") is True
        import time; time.sleep(0.02)
        assert _is_provider_unhealthy("openrouter") is False"""

text = re.sub(
    r'[ \t]*def test_ttl_expiry_evicts\(self\):\n(?:[ \t]+.*\n)*?[ \t]+assert _is_provider_unhealthy\("openrouter"\) is True[^\n]*\n(?:[ \t]+assert _is_provider_unhealthy\("openrouter"\) is False[^\n]*\n)?',
    replacement + "\n",
    text,
    count=1
)

with open("tests/agent/test_auxiliary_client.py", "w", encoding="utf-8") as f:
    f.write(text)
