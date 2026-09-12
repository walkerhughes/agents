"""Print a Supabase Auth access token; prompt for credentials on the terminal."""

import getpass
import json
import os
import sys
import urllib.error
import urllib.request

project_ref = os.environ.get("SUPABASE_PROJECT_REF", "tteazpolsuwfxqqqksoj")
key = os.environ.get("SUPABASE_ANON_KEY")
if not key:
    sys.exit("Set SUPABASE_ANON_KEY to the project's anon key.")
with open("/dev/tty", "r+") as terminal:
    terminal.write("Email: ")
    terminal.flush()
    email = terminal.readline().strip()
password = getpass.getpass("Password: ")
request = urllib.request.Request(
    f"https://{project_ref}.supabase.co/auth/v1/token?grant_type=password",
    data=json.dumps({"email": email, "password": password}).encode(),
    headers={"apikey": key, "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        print(json.load(response)["access_token"])
except urllib.error.HTTPError as error:
    sys.exit(f"Sign-in failed (HTTP {error.code}). Check your credentials.")
except urllib.error.URLError:
    sys.exit("Could not reach Supabase Auth. Check your connection.")
