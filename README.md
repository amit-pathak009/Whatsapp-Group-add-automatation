# WhatsApp Group Participant Adder

Automate adding participants to WhatsApp groups via WhatsApp Web using Selenium. This script helps efficiently add multiple participants from a list of phone numbers, with support for batch processing, retries, manual intervention, and progress tracking.

---

## Features

- **Automated participant addition:** Adds phone numbers from a provided list to a specified WhatsApp group.
- **Batch processing:** Adds participants in configurable batch sizes to prevent overwhelming WhatsApp’s interface.
- **Phone number normalization:** Automatically formats phone numbers, adding default country codes if missing.
- **Flexible participant matching:** Matches phone numbers with multiple format variants for better accuracy.
- **Retry mechanism:** Retries critical steps like participant search and selection to improve reliability.
- **Manual fallback support:** When automatic matching fails, allows you to manually select participants and stores selections for reuse.
- **Progress tracking and resuming:** Saves processed participants so you can stop and resume without duplicating work.
- **Comprehensive logging:** Logs all operations, errors, and batch summaries to a log file.
- **Status reporting:** Generates reports per batch on who was added, invited, already in group, or not added.
- **Customizable UI interaction texts:** Easily adapt the script to changes in WhatsApp Web UI labels like “Invite” or “Already added”.
- **Interactive batch size control:** Choose batch sizes interactively before processing each batch.
- **Cross-platform support:** Works on any OS with Python, Chrome, and ChromeDriver installed.

---

## Prerequisites

- Python 3.7 or later
- [Selenium](https://pypi.org/project/selenium/)
- Google Chrome browser installed
- Matching [ChromeDriver](https://sites.google.com/chromium.org/driver/) version for your Chrome
- WhatsApp Web logged in through a Chrome user profile (configured via `--user-data-dir` option)

---

## Installation

1. Clone or download this script.
2. Install Selenium via pip:

   ```bash
   pip install selenium
```

3. Download ChromeDriver matching your Chrome browser version and ensure it’s accessible in your system’s PATH or specify the path in the script.
4. Set the Chrome user data directory path in the script to your WhatsApp Web profile folder to keep the session active:

   ```python
   options.add_argument("--user-data-dir=/path/to/your/whatsapp/profile")
   ```

---

## Usage

Run the script from the command line as:

```bash
python add_participants.py "<group_name>" <participants_file>
```

* `<group_name>` — Exact name of the WhatsApp group where participants will be added.
* `<participants_file>` — Text file path containing one phone number per line.

Example:

```bash
python add_participants.py "Friends Group" participants.txt
```

---

## How It Works

1. **Launch WhatsApp Web:** Opens Chrome with your WhatsApp profile loaded.
2. **Locate the Group:** Finds and opens the group chat by its name.
3. **Process Participants:**

   * Reads phone numbers from the file.
   * Normalizes numbers and checks for duplicates.
   * Processes participants in batches, each batch size configurable interactively.
4. **Search & Select:**

   * Searches participants using multiple phone number formats.
   * Automatically clicks the correct contact or invites them.
   * If unable to automatically select, prompts manual selection and saves it for future.
5. **Add Participants:**

   * Once a batch is selected, prompts you to manually confirm addition in WhatsApp Web.
   * Saves the processed participants to allow resuming later.
6. **Logging and Reporting:**

   * Detailed logs maintained in `process_log.txt`.
   * Batch reports saved in respective text files.

---

## Configuration Options

* **`DEFAULT_COUNTRY_CODE`**: Set your default country code for phone numbers without one (e.g., "+91").
* **`MAX_MEMBERS`**: Default maximum number of participants to add per batch (default: 5).
* **`RETRY_ATTEMPTS`**: Number of retries for critical UI actions (default: 2).
* **`ALREADY_IN_GROUP_TEXT`** and **`INVITE_TEXT`**: UI texts to detect existing members or invite buttons, which you can adjust if WhatsApp Web updates.

---

## Files Created

* **`process_log.txt`** — Detailed log of actions and errors.
* **`manual_selections.json`** — Stores manual selections for participants to avoid repeated manual work.
* **`resume.json`** — Tracks participants already processed to support resuming.
* **`added_<batch>.txt`** — Participants successfully added this batch.
* **`already_in_group_<batch>.txt`** — Participants already in the group.
* **`invited_<batch>.txt`** — Participants invited to join.
* **`not_added_<batch>.txt`** — Participants failed to be added or invited.

---

## Tips & Troubleshooting

* **ChromeDriver mismatch:** Make sure ChromeDriver version matches your Chrome browser.
* **WhatsApp Web UI changes:** If the script fails to find elements, update the XPaths or UI label constants.
* **Manual selection prompt:** When automatic selection fails, carefully select the right contact in WhatsApp Web before continuing.
* **Use a dedicated WhatsApp profile folder:** Avoid conflicts by using a dedicated Chrome user data directory for WhatsApp Web sessions.
* **Network stability:** Ensure a stable internet connection to avoid timeouts.

---

## Disclaimer

* This tool automates interactions with WhatsApp Web and may violate WhatsApp’s terms of service. Use responsibly.
* The author is not responsible for any account suspension or data loss.
* Use at your own risk.

---

## License

MIT License

---

## Author

Created and maintained by 4M17

---

Feel free to report issues or contribute improvements!
