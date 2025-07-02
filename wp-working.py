import sys
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Configuration
ALREADY_IN_GROUP_TEXT = "Already added to community"  # Adjust based on WhatsApp UI
INVITE_TEXT = "Invite"  # Adjust based on WhatsApp UI
DEFAULT_COUNTRY_CODE = "+91"  # Adjust as needed
MAX_MEMBERS = 5  # Default maximum participants per batch
RETRY_ATTEMPTS = 2  # Number of retries for critical operations
SEARCH_RESULT_TIMEOUT = 15  # Timeout for search results
LOG_FILE = "process_log.txt"  # Log file for tracking
MANUAL_SELECTIONS_FILE = "manual_selections.json"  # Store manual selections
RESUME_FILE = "resume.json"  # Track processed participants

# Function to normalize phone numbers
def normalize_phone_number(phone):
    """Normalize phone numbers by keeping digits and adding country code if needed."""
    cleaned = ''.join(c for c in phone if c.isdigit())
    if not cleaned.startswith('+'):
        cleaned = DEFAULT_COUNTRY_CODE + cleaned
    return cleaned

# Function to get phone number variants for matching
def get_formatted_variants(phone_number):
    """Generate possible phone number variants for flexible matching."""
    variants = []
    if phone_number.startswith('+'):
        variants.append(phone_number[1:])  # e.g., "918989568523"
    variants.append(phone_number.replace('+', ''))  # e.g., "918989568523"
    if len(phone_number) > 10:
        variants.append(phone_number[-10:])  # e.g., "8989568523"
    return [v.lower() for v in variants]

# Function to load manual selections
def load_manual_selections():
    """Load previously stored manual selections from JSON file."""
    try:
        with open(MANUAL_SELECTIONS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Function to save manual selections
def save_manual_selections(manual_selections):
    """Save manual selections to JSON file."""
    with open(MANUAL_SELECTIONS_FILE, 'w') as f:
        json.dump(manual_selections, f, indent=4)

# Function to load processed participants
def load_processed_participants():
    """Load processed participants from resume.json."""
    if os.path.exists(RESUME_FILE):
        with open(RESUME_FILE, 'r') as f:
            return set(json.load(f))
    return set()

# Function to save processed participants
def save_processed_participants(processed):
    """Save processed participants to resume.json."""
    with open(RESUME_FILE, 'w') as f:
        json.dump(list(processed), f)

# Function to ensure search bar is accessible
def ensure_search_bar(driver, wait):
    """Check if the search bar is accessible; if not, prompt user to recapture it."""
    global search_bar
    def is_element_accessible(element):
        try:
            element.send_keys("")
            return True
        except Exception:
            return False

    if search_bar is None or not is_element_accessible(search_bar):
        print("\nPlease perform these steps manually:")
        print("1. Click the group name at the top to open group info.")
        print("2. Click 'Add participant'.")
        print("3. Click the search bar to focus it, then press Enter in the terminal.")
        input("Press Enter when ready...")
        try:
            search_bar = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']")))
            print("Search bar captured successfully.")
        except Exception as e:
            print(f"Error capturing search bar: {e}")
            with open(LOG_FILE, "a") as log_file:
                log_file.write(f"Error capturing search bar: {e}\n")
            driver.quit()
            sys.exit(1)
    return search_bar

# Command-line argument validation
if len(sys.argv) != 3:
    print("Usage: python add_participants.py <group_name> <participants_file>")
    sys.exit(1)

group_name = sys.argv[1]
participants_file = sys.argv[2]

# Read participants from file
try:
    with open(participants_file, 'r') as f:
        all_participants = [normalize_phone_number(line.strip()) for line in f if line.strip()]
    if not all_participants:
        print("Error: The participants file is empty.")
        sys.exit(1)
except FileNotFoundError:
    print(f"Error: File '{participants_file}' not found.")
    sys.exit(1)

# Load processed participants and manual selections
processed_participants = load_processed_participants()
manual_selections = load_manual_selections()

# Set up Chrome WebDriver with user profile
options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=/home/kali/Documents/Document/I4C/Cyber-Commandos/WhatsAppProfile")  # Update this path
driver = webdriver.Chrome(options=options)
driver.get("https://web.whatsapp.com")

# Wait for WhatsApp Web to load
print("Loading WhatsApp Web...")
wait = WebDriverWait(driver, 60)
try:
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.two")))
    print("Logged in successfully.")
except Exception as e:
    print(f"Login failed: {e}")
    driver.quit()
    sys.exit(1)

# Locate and click the group
try:
    group_element = wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[@title='{group_name}']")))
    group_element.click()
    print(f"Group '{group_name}' found and clicked.")
except Exception as e:
    print(f"Error finding group '{group_name}': {e}")
    driver.quit()
    sys.exit(1)

# Initialize batch variables
current_index = 0
batch_number = 1
search_bar = None  # Global search_bar variable

# Process participants in batches
while current_index < len(all_participants):
    # Skip already processed participants
    while current_index < len(all_participants) and all_participants[current_index] in processed_participants:
        current_index += 1
    if current_index >= len(all_participants):
        print("All participants have been processed.")
        break

    # Ensure search bar is accessible before starting batch
    search_bar = ensure_search_bar(driver, wait)

    # Ask for batch size at the beginning of each batch
    batch_size_input = input(f"Enter the number of participants for batch {batch_number} (default {MAX_MEMBERS}): ").strip()
    if batch_size_input:
        try:
            current_max_members = int(batch_size_input)
            if current_max_members <= 0:
                print("Invalid number. Using default.")
                current_max_members = MAX_MEMBERS
        except ValueError:
            print("Invalid input. Using default.")
            current_max_members = MAX_MEMBERS
    else:
        current_max_members = MAX_MEMBERS

    # Initialize batch variables
    added = []
    already_in_group = []
    invited = []
    not_added = []
    selected_count = 0

    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"\n--- Batch {batch_number} started with {current_max_members} participants ---\n")

        while True:
            # Process participants up to the current_max_members
            while selected_count < current_max_members and current_index < len(all_participants):
                phone_number = all_participants[current_index]
                if phone_number in processed_participants:
                    current_index += 1
                    continue

                log_file.write(f"\nProcessing: {phone_number}\n")
                success = False

                # Step 1: Try stored manual selection
                if phone_number in manual_selections:
                    participant_text = manual_selections[phone_number]
                    try:
                        participant = driver.find_element(By.XPATH, f"//div[@role='listitem' and contains(., '{participant_text}')]")
                        participant.click()
                        selected_count += 1
                        added.append(phone_number)
                        log_file.write(f"Selected {phone_number} using stored manual selection: {participant_text}\n")
                        print(f"Selected {phone_number} using stored manual selection.")
                        success = True
                    except Exception as e:
                        log_file.write(f"Failed stored manual selection for {phone_number}: {e}\n")
                        print(f"Failed stored manual selection for {phone_number}: {e}")

                # Step 2: Automatic selection
                if not success:
                    for attempt in range(RETRY_ATTEMPTS):
                        try:
                            search_bar.send_keys(Keys.CONTROL + "a", Keys.DELETE)
                            search_bar.send_keys(phone_number)
                            time.sleep(1)
                            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='listitem']")))
                            participants_list = driver.find_elements(By.XPATH, "//div[@role='listitem']")
                            variants = get_formatted_variants(phone_number)

                            for participant in participants_list:
                                text = participant.text.replace(' ', '').lower()
                                for variant in variants:
                                    if variant in text:
                                        if participant.find_elements(By.XPATH, f".//div[contains(text(), '{ALREADY_IN_GROUP_TEXT}')]"):
                                            already_in_group.append(phone_number)
                                            log_file.write(f"Skipped {phone_number}: Already in group.\n")
                                            print(f"Skipped {phone_number}: Already in group.")
                                            processed_participants.add(phone_number)
                                            success = True
                                        else:
                                            try:
                                                invite_button = participant.find_element(By.XPATH, f".//div[contains(text(), '{INVITE_TEXT}')]")
                                                invite_button.click()
                                                invited.append(phone_number)
                                                log_file.write(f"Invited {phone_number}.\n")
                                                print(f"Invited {phone_number}.")
                                                processed_participants.add(phone_number)
                                                success = True
                                            except NoSuchElementException:
                                                participant.click()
                                                selected_count += 1
                                                added.append(phone_number)
                                                log_file.write(f"Selected {phone_number} automatically.\n")
                                                print(f"Selected {phone_number} automatically.")
                                                success = True
                                        break
                                if success:
                                    break

                            if not success:
                                raise Exception("No matching participant found")

                        except (TimeoutException, Exception) as e:
                            if attempt < RETRY_ATTEMPTS - 1:
                                log_file.write(f"Retry {attempt + 1}/{RETRY_ATTEMPTS} for {phone_number}: {e}\n")
                                print(f"Retry {attempt + 1}/{RETRY_ATTEMPTS} for {phone_number}: {e}")
                                time.sleep(2)
                            else:
                                log_file.write(f"Failed to process {phone_number} after {RETRY_ATTEMPTS} attempts: {e}\n")
                                print(f"Failed to process {phone_number} after {RETRY_ATTEMPTS} attempts: {e}")
                                print(f"\nFailed to select {phone_number} automatically. Please select the correct participant in WhatsApp, then press Enter...")
                                input("Press Enter after manual selection...")
                                try:
                                    checked_checkbox = driver.find_element(By.XPATH, "//input[@type='checkbox' and @checked]")
                                    participant_element = checked_checkbox.find_element(By.XPATH, "./ancestor::div[@role='listitem']")
                                    participant_text = ' '.join(participant_element.text.split())
                                    manual_selections[phone_number] = participant_text
                                    save_manual_selections(manual_selections)
                                    log_file.write(f"Stored manual selection for {phone_number}: {participant_text}\n")
                                    print(f"Stored manual selection for {phone_number}.")
                                    selected_count += 1
                                    added.append(phone_number)
                                    success = True
                                except Exception as e:
                                    log_file.write(f"Failed to capture manual selection for {phone_number}: {e}\n")
                                    print(f"Failed to capture manual selection: {e}")
                                    not_added.append(phone_number)
                                break

                if not success:
                    not_added.append(phone_number)
                current_index += 1

            # Check if we can extend the batch
            if current_index >= len(all_participants) or selected_count >= current_max_members:
                break

            extend_response = input(f"\nDo you want to increase the number of participants in batch {batch_number}? (yes/no): ").strip().lower()
            if extend_response == 'yes':
                try:
                    new_max_members = int(input("Enter the new number of participants for this batch: "))
                    if new_max_members > selected_count:
                        current_max_members = new_max_members
                        print(f"Batch {batch_number} extended to {current_max_members} participants.")
                        # Ensure search bar is accessible before continuing
                        search_bar = ensure_search_bar(driver, wait)
                    else:
                        print(f"New number must be greater than the current selected count ({selected_count}).")
                        break
                except ValueError:
                    print("Invalid input.")
                    break
            else:
                break

        # Confirm addition for all participants in this batch
        if added:
            print(f"\nSelected {len(added)} participants. Please manually click 'Add' in WhatsApp.")
            input("Press Enter after adding participants...")
            processed_participants.update(added)
            save_processed_participants(processed_participants)
            print("Participants marked as processed.")

        # Write batch results
        for status, numbers, filename in [
            ("added", added, f"added_{batch_number}.txt"),
            ("already_in_group", already_in_group, f"already_in_group_{batch_number}.txt"),
            ("invited", invited, f"invited_{batch_number}.txt"),
            ("not_added", not_added, f"not_added_{batch_number}.txt")
        ]:
            with open(filename, "w") as f:
                f.writelines(f"{num}\n" for num in numbers)

        # Batch summary
        log_file.write(f"\nSummary for batch {batch_number}:\n")
        log_file.write(f"Added: {len(added)}\n")
        log_file.write(f"Already in group: {len(already_in_group)}\n")
        log_file.write(f"Invited: {len(invited)}\n")
        log_file.write(f"Not added: {len(not_added)}\n")
        print(f"\nSummary for batch {batch_number}:")
        print(f"Added: {len(added)}")
        print(f"Already in group: {len(already_in_group)}")
        print(f"Invited: {len(invited)}")
        print(f"Not added: {len(not_added)}")

    # Ask to continue to the next batch
    response = input("\nContinue to next batch? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Stopping script. Progress saved in resume.json.")
        break

    batch_number += 1

# Cleanup
driver.quit()
print("Script execution completed.")
