# IntelliForm: Intelligent Automated Form-Filling Agent

IntelliForm opens a web form in a controlled browser, finds the fields, proposes values from **your saved profile**, lets **you** confirm anything uncertain, fills the form, checks what the page really shows, and then **stops**. You review the form and press Submit yourself. IntelliForm never clicks Submit, Apply, Register or Pay.

It runs only on your own computer (`127.0.0.1`), needs no paid API and no API keys.

> **Please read the honest limits first**
> * It is tested against the six practice forms in `test_forms/` that ship with it. It has **not** been tested on real public websites (see `docs/tested_sites.md`). Do not assume it works on every hackathon, scholarship or job site.
> * It does not solve CAPTCHAs or sign in for you, and never types passwords.
> * Your profile is saved in a plain local file. It is **not** encrypted, there is no login, and it is **not** a secure multi-user or cloud store. Use it on your own computer only.
> * One run at a time. A second run is refused until the first finishes or is cancelled.

---

## 1. Install (Windows 11, step by step)

### 1.1 Install Python 3.12
1. Go to <https://www.python.org/downloads/> and download **Python 3.12**.
2. Run the installer. **Tick "Add python.exe to PATH"** on the first screen, then click *Install Now*.
3. Open **PowerShell** (Start menu, type `PowerShell`) and check:
   ```powershell
   python --version
   ```
   You should see `Python 3.12.x`. (Only 3.12 was tested; 3.10 or newer should also work.)

### 1.2 Extract the ZIP
Right-click `INTELLIFORM-FINAL.zip` → **Extract All…** → choose a folder such as `C:\Users\<you>\Documents`. You get one folder called `INTELLIFORM`.

### 1.3 Open the folder in VS Code
VS Code → **File → Open Folder…** → select `INTELLIFORM`. Then **Terminal → New Terminal**. A PowerShell panel opens already inside the project folder. Check with:
```powershell
dir
```
You should see `app.py`, `requirements.txt` and `README.md`. **All later commands are typed here.** If you do not see `app.py`, you are in the wrong folder; use `cd` to move into `INTELLIFORM`.

### 1.4 Create a virtual environment (a private box for this project's packages)
```powershell
python -m venv .venv
```

### 1.5 Activate it
```powershell
.\.venv\Scripts\Activate.ps1
```
The line now starts with `(.venv)`. If PowerShell says *running scripts is disabled*, run this once and try again:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Activate again every time you open a new terminal.

### 1.6 Install the requirements
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 1.7 Install the browser Playwright controls
```powershell
python -m playwright install chromium
```
This downloads a separate Chromium (about 150 MB) used only by IntelliForm. It does not touch your normal browser.

---

## 2. Run it

```powershell
python app.py
```
You should see `IntelliForm is running. Open http://127.0.0.1:5000`. Leave this window open. Then open <http://127.0.0.1:5000> in your normal browser.

**To stop:** click the terminal and press `Ctrl+C`. To leave the virtual environment: `deactivate`.

## 3. Your first run (try the practice forms)

1. **Profile** page: fill in at least the three *Required* fields (full name, email, phone) and press *Save profile*. Add more (country, college, degree…) so more fields can be filled. Empty optional fields are never invented.
2. **Overview** page: click *Use this form* next to `scholarship.html`. This opens **Agent run** with the address filled in.
3. Press **Start agent**. A Chromium window opens. The stage rail shows real progress.
4. **Review the proposed values.** Every field the agent found is listed with the profile value it suggests and a match percentage. Amber rows are uncertain: tick the box only if you agree. Dropdowns list the real options found on the page. Press **Fill selected fields**.
5. If required fields are still empty (for example the consent checkbox) the agent **asks you**. Provide a value, or tick *Skip*.
6. The agent shows **Results**: which fields were filled and whether the page really shows the value (*Verified on the page*).
7. Look at the Chromium window. Fix anything wrong. Press the form's own Submit button yourself if you want to (the practice forms just say they were submitted).
8. Back in the dashboard press **Finish and close browser**.

You can press **Cancel run** at any time. Cancelling closes the browser.

Where things are stored:
| What | Where |
|---|---|
| Profile | `data\profile.json` (plain text, not encrypted) |
| Technical log (no personal values) | `logs\intelliform.log` |

Delete the profile with the *Delete profile* button, or delete `data\profile.json`.

## 4. Run the automated tests

Open a **second** terminal in VS Code (Terminal → New Terminal), activate the environment (`.\.venv\Scripts\Activate.ps1`), then:
```powershell
python -m pytest
```
The tests start their own server and their own headless Chromium, so you can run them while the app is stopped. They take roughly one minute. Results from the build environment are in `docs/test_results.md`. Run it yourself to confirm on your machine.

## 5. What it can and cannot fill

| Supported | Not supported (left for you) |
|---|---|
| Text, email, phone, URL, number, date, text area | Passwords (never typed) |
| Native dropdowns (`<select>`), including dependent ones that fill after another field | File uploads |
| Custom ARIA dropdowns (`role="combobox"` / listbox) that list their options when opened | Dropdowns that only load options while you type |
| Radio groups, single checkboxes, checkbox groups | Rich widgets: date pickers drawn on canvas, shadow DOM, contenteditable boxes |
| Forms inside iframes, forms drawn by JavaScript after load | CAPTCHAs, sign-in pages (you do these by hand in the window) |

Checkboxes (including "I agree" and consent boxes) are **never** ticked automatically.

## 6. Safety rules built in

* Never submits: three independent layers (see `docs/architecture.md`).
* Only public `http`/`https` addresses are accepted. `localhost`, private networks, link-local and cloud-metadata addresses are refused, DNS is checked, and every redirect hop of a page load is checked.
* The dashboard only listens on `127.0.0.1` and rejects requests from other websites.
* Uncertain matches are never filled until you confirm them. Dates are never guessed. No dropdown option is picked "just because it is first".
* No API keys, passwords or personal data are in this project. Profile data and logs are excluded by `.gitignore`.

## 7. Project layout

```
app.py                  starts the local server (Flask)
config.py               settings (all have safe defaults; see .env.example)
profile_manager.py      load/save/delete profile.json
modules/                form_analyzer, field_mapper, validator, decisions, task_manager
browser/                browser_controller.py (all Playwright code)
routes/                 profile_routes.py, agent_routes.py (JSON API)
dashboard/              index.html, styles.css, app.js
test_forms/             six local practice forms
tests/                  pytest suite
docs/                   architecture, troubleshooting, tested sites, test results
```

## 8. Common problems
See `docs/troubleshooting.md`. The three most common: PowerShell script policy (step 1.5), forgetting `python -m playwright install chromium` (step 1.7), and port 5000 already in use (set `INTELLIFORM_PORT=5001` in a `.env` file, copied from `.env.example`).
