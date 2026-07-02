"""SageMaker container entrypoint: `docker run <image> serve`."""

from __future__ import annotations

import subprocess
import sys


def main() -> None:
  if len(sys.argv) >= 2 and sys.argv[1] == "serve":
    raise SystemExit(
        subprocess.call(
            [
                "gunicorn",
                "--bind",
                "0.0.0.0:8080",
                "--workers",
                "1",
                "serve:app",
                "--chdir",
                "/opt/ml/code",
            ]
        )
    )
  print("Expected: serve", file=sys.stderr)
  raise SystemExit(1)


if __name__ == "__main__":
  main()
