# CLICK THESE — no searching

Do these in order. Each link opens the right page. Confirm / Allow / Create only.

---

## 1) Snowflake (login + worksheet)

1. Open and sign in:  
   **https://nichzfb-tm14717.snowflakecomputing.com**

2. After login, open Worksheets (left menu) → **+ Worksheet**.

3. When I say “approve browser”, a second tab may open for SSO/approve — click **Allow / Continue**.

You do **not** need to find docs. Stay logged into Snowflake in one browser tab.

---

## 2) Databricks — revoke old token + new token (1 minute)

1. Open workspace:  
   **https://dbc-fab0ac6b-3d42.cloud.databricks.com**

2. Click your user icon (bottom-left) → **Settings** → **Developer** → **Access tokens**  
   Direct-ish path after login:  
   **https://dbc-fab0ac6b-3d42.cloud.databricks.com/settings/user/developer/access-tokens**

3. **Revoke** the old token that was pasted in chat.

4. **Generate new token** → copy it **only into**  
   `d:\IIMA\Portfolio\cfpb-data-platform\.env`  
   as:
   ```
   DATABRICKS_HOST=https://dbc-fab0ac6b-3d42.cloud.databricks.com
   DATABRICKS_TOKEN=<paste-new-token-here>
   ```
   Do **not** paste the token back into Cursor chat.

---

## 3) Databricks — upload folder (when I ask)

1. **https://dbc-fab0ac6b-3d42.cloud.databricks.com/#workspace**  
   or Catalog / Volumes / DBFS FileStore as shown in your Free Edition UI.

2. Create folder `cfpb/complaints` and upload Parquet when I say “upload now”.

---

## 4) GitHub (when project is green)

Repo: **https://github.com/marcelinobrgnz/Portfolio**

I can push the `cfpb-data-platform/` folder via CLI if you say **Y** to push (reply `GitHub: Y`).

---

## What you will click when I run Snowflake from CLI

- Browser popup / tab: **Allow this app to access Snowflake**  
- That’s it for auth (Option B — externalbrowser).

No password hunting. No OAuth app setup required for today.
