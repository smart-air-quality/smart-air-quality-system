"""
Thin entrypoint on the device filesystem root.

Upload from repo:
  - this file → /main.py
  - entire `aqmon/` package → /aqmon/
  - config.example → /config.py (see iot/config/config.example.py)
"""

from aqmon.run import run

if __name__ == "__main__":
    run()
