# Ransomware Detection & Recovery Module - Implementation Plan

## Overview
Build a production-quality ransomware analysis module with demo simulator, detection engine, and recovery capabilities — fully integrated into the existing CyberShield Flask project without breaking UPI Fraud or Cookie Protection modules.

---

## 1. Database Models (`app/models.py`)

### New Tables:
- **`RansomwareScanHistory`** — stores every file scan (filename, extensions, sha256, entropy, risk_score, status, family, reasons, recommendations, timestamp, user_id)
- **`EncryptedFile`** — files encrypted by the demo simulator (original_filename, encrypted_filename, sha256, encryption_key, encryption_timestamp, status)
- **`EncryptionKey`** — maps encryption key to file for decryption (key_id, file_hash, key_bytes, created_at)

---

## 2. Utility Modules (`app/utils/`)

### `entropy_checker.py`
- Calculate Shannon entropy of file bytes
- Threshold: >7.5 = very high entropy (likely encrypted)

### `hash_checker.py`
- Compute SHA-256 hash of any file
- Compare against known malicious hashes (demo malware hash DB)

### `file_analyzer.py`
- Orchestrate full analysis:
  - Read file bytes, magic bytes (first 4-8 bytes)
  - Detect double extensions (.pdf.exe, .jpg.exe)
  - Known ransomware extensions (.locked, .encrypted, .lockbit, .wcry, .crypt)
  - Compute entropy via `entropy_checker`
  - Compute SHA-256 via `hash_checker`
  - Check if file was encrypted by demo simulator (look up hash in `EncryptedFile` table)
  - Return structured analysis result

### `demo_encryptor.py`
- Encrypt a file using `cryptography.fernet.Fernet`
- Save key to `EncryptionKey` table
- Rename file with `.locked` extension
- Record in `EncryptedFile` table

### `demo_decryptor.py`
- Retrieve encryption key from DB using file hash
- Decrypt file using Fernet
- Restore original filename
- Save to `Recovered Files` folder

### `risk_engine.py` (NEW - for ransomware)
- New risk engine specific to ransomware (separate from UPI risk_engine)
- Score 0-100 based on:
  - Known ransomware extension (+30)
  - Executable extension (+15)
  - Double extension (+20)
  - Very high entropy >7.5 (+25)
  - Known malicious hash (+20)
  - Demo ransomware match (+40)
- Status: 0-30 Safe, 31-70 Medium Risk, 71-100 High Risk

---

## 3. Routes (`app/blueprints/modules/routes.py`)

### POST `/module/ransomware` (updated)
- Accept file upload (not just text input)
- Save file to `uploads/` folder
- Run full file analysis pipeline
- Save scan to `RansomwareScanHistory`
- Return analysis results to template

### POST `/module/ransomware/decrypt/<scan_id>`
- Verify file was encrypted by demo simulator
- Retrieve encryption key
- Decrypt and save to `Recovered Files/`
- Update scan status to "Recovered"

### GET `/module/ransomware/download/<scan_id>`
- Serve the recovered file for download

### POST `/module/ransomware/encrypt` (demo simulator)
- Accept file upload for demo encryption
- Run `demo_encryptor` on the file
- Provide download of encrypted file + display key info

### GET `/module/ransomware/stats`
- JSON endpoint for dashboard statistics

---

## 4. Templates

### `app/templates/modules/ransomware.html` (complete rewrite)
**Left Column - Analyze:**
- File upload with drag-and-drop
- Animated scanning effect (CSS/JS)
- Demo Ransomware Simulator section (encrypt file)

**Right Column - Results:**
- Circular risk meter (SVG/CSS progress ring)
- File details card (name, extensions, size, hash, entropy)
- Encryption status + detected family
- Risk score with color coding
- Decrypt button (if demo ransomware)
- Recommendations list
- Download recovered file link

---

## 5. Static Files

### `static/css/style.css` (additions)
- Circular progress meter styles
- Scanning animation keyframes
- Drag-and-drop zone styles
- Dashboard stats cards

### `static/js/main.js` (additions)
- File upload with preview
- Animated scanning overlay
- AJAX polling for scan progress
- Risk meter animation

---

## 6. Dashboard Integration

### `app/templates/dashboard.html` (update)
- Add ransomware statistics cards:
  - Total Files Scanned
  - Encrypted Files Found
  - Recovered Files
  - High Risk Files
  - Recovery Success Rate

### JSON stats endpoint for dashboard

---

## 7. Dependencies

Add to `requirements.txt`:
```
cryptography==42.0.0
```

---

## 8. File Structure Changes

```
cyber/
├── app/
│   ├── utils/
│   │   ├── file_analyzer.py      (NEW)
│   │   ├── hash_checker.py       (NEW)
│   │   ├── entropy_checker.py    (NEW)
│   │   ├── demo_encryptor.py     (NEW)
│   │   ├── demo_decryptor.py     (NEW)
│   │   └── risk_engine.py        (NEW - ransomware version)
│   ├── uploads/                  (NEW - folder for uploaded files)
│   ├── recovered/                (NEW - folder for recovered files)
│   └── templates/modules/
│       └── ransomware.html       (REWRITE)
│   └── models.py                 (UPDATE - add 3 new tables)
│   └── blueprints/modules/
│       └── routes.py             (UPDATE - add ransomware routes)
├── static/
│   └── js/main.js                (UPDATE)
│   └── css/style.css             (UPDATE)
└── requirements.txt              (UPDATE)
```

---

## Implementation Order

1. Install `cryptography` dependency
2. Add new DB models to `models.py`
3. Create utility modules (entropy, hash, file_analyzer, encryptor, decryptor, risk engine)
4. Update `routes.py` with new ransomware endpoints
5. Rewrite `ransomware.html` template
6. Update `style.css` with new styles
7. Update `main.js` with new interactivity
8. Update `dashboard.html` with ransomware stats
9. Test full workflow

