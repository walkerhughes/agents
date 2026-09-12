"""Exercise the token helper without network requests or actual credentials."""

import contextlib
import io
import json
import os
import runpy
from pathlib import Path
from unittest.mock import patch

script = Path(__file__).resolve().parents[1] / "scripts" / "login.py"
output = io.StringIO()
response = io.BytesIO(json.dumps({"access_token": "test-jwt"}).encode())
with (
    patch.dict(os.environ, {"SUPABASE_ANON_KEY": "test-key"}, clear=True),
    patch("builtins.open") as tty,
    patch("getpass.getpass", return_value="secret-password"),
    patch("urllib.request.urlopen", return_value=response) as urlopen,
    contextlib.redirect_stdout(output),
):
    tty.return_value.__enter__.return_value.readline.return_value = "user@example.com\n"
    runpy.run_path(str(script), run_name="__main__")
    request = urlopen.call_args.args[0]
    assert json.loads(request.data) == {"email": "user@example.com", "password": "secret-password"}
    assert request.headers["Apikey"] == "test-key"
    assert urlopen.call_args.kwargs["timeout"] == 30
assert output.getvalue() == "test-jwt\n", "stdout must contain only the JWT"

with patch.dict(os.environ, {}, clear=True):
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as error:
        assert "SUPABASE_ANON_KEY" in str(error)
    else:
        raise AssertionError("Missing configuration must fail")
print("PASS: token helper uses Auth and prints only the token; missing key fails")
