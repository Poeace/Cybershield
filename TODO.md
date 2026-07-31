# Encryption Key Email & Download Fix - TODO

## Step 1: `app/utils/ransomware_simulator.py`
- [x] Add imports for email sending (mail, Message, User, current_app)
- [x] Modify `encrypt_user_file()`: Send encryption key to user's email after encryption
- [x] Fix `list_encrypted_files()`: Return both "encrypted" and "restored" status files

## Step 2: `app/templates/modules/ransomware.html`
- [x] Update frontend to show "Key emailed" notification after encryption
- [x] `loadRestoredFiles()` will now properly show restored files for download via the updated backend

## Step 3: Test
- [ ] Run the Flask app and verify:
  - [ ] Encryption key is sent to user's registered email after file encryption
  - [ ] Email notification appears on the UI after successful encryption
  - [ ] After decryption, the restored file appears in the Download section (Step 3)
  - [ ] Download link works and serves the decrypted file

