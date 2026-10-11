"""Snowflake auth test — password preferred; externalbrowser fallback."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import snowflake.connector


def main() -> None:
    account = os.environ["SNOWFLAKE_ACCOUNT"]
    user = os.environ["SNOWFLAKE_USER"]
    password = os.getenv("SNOWFLAKE_PASSWORD", "").strip()
    role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")

    kwargs = {
        "account": account,
        "user": user,
        "role": role,
    }

    if password:
        print("Connecting with password auth...")
        kwargs["password"] = password
        kwargs["authenticator"] = "snowflake"
    else:
        print("No SNOWFLAKE_PASSWORD in .env — trying externalbrowser...")
        print("If this fails with SAML error, set a password in .env instead.")
        kwargs["authenticator"] = "externalbrowser"

    conn = snowflake.connector.connect(**kwargs)
    cur = conn.cursor()
    cur.execute(
        "SELECT CURRENT_ACCOUNT_NAME(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_REGION()"
    )
    print("OK:", cur.fetchone())
    conn.close()
    print("Snowflake auth OK")


if __name__ == "__main__":
    main()
