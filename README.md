# 🛡️ CyberShield – Cybersecurity Protection Platform (Live: https://cybershield-3-g0n2.onrender.com)

CyberShield is a web-based cybersecurity application developed using **Python Flask** that helps users understand and protect themselves from common cyber threats through interactive security modules. It provides practical demonstrations of ransomware recovery, cookie security analysis, and UPI fraud detection in a safe and educational environment.

## 📌 Features

### 🔐 User Authentication
- User Registration & Login
- Secure Password Hashing
- Session Management
- Admin Login

### 💳 UPI Fraud Detection
- Validate UPI IDs
- Detect suspicious or malformed UPI IDs
- Generate fraud detection results

### 🦠 Ransomware Protection
- Upload important files
- Create encrypted backups
- SHA-256 integrity verification
- Secure backup storage
- Restore files from encrypted backups
- Automatic deletion of temporary uploaded files
- Download incident reports

### 🍪 Cookie Protection
- Cookie integrity scanner
- Secure, HttpOnly & SameSite validation
- Session security analysis
- Cookie tampering detection
- Security score generation
- Risk assessment

### 📊 Security Dashboard
- Live registered user count
- Live threat detection statistics
- Protected files count
- Restored files count
- Security activity timeline
- Admin analytics dashboard

### 📄 Reports
- PDF incident reports
- Security logs
- Recovery history

# 🚀 Technologies Used

## Backend
- Python
- Flask
- SQLAlchemy
- SQLite

## Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap 5

## Security
- SHA-256 Hashing
- Fernet (AES Encryption)
- Secure Session Cookies
- Password Hashing
- Input Validation

# 📂 Project Structure

```
CyberShield/
│
├── app.py
├── requirements.txt
├── database.db
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│
├── templates/
│
├── uploads/
├── backups/
├── encrypted/
├── restored/
├── reports/
│
└── README.md
```
# 🔄 Workflow

### Ransomware Protection

```
User Upload
      │
      ▼
Temporary Upload
      │
      ▼
Create Encrypted Backup
      │
      ▼
Delete Temporary Upload
      │
      ▼
Backup Ready for Restore
      │
      ▼
Restore File
      │
      ▼
Generate Security Report
```

# 🔒 Security Features

- AES Encrypted Backups
- SHA-256 Integrity Verification
- Secure Session Management
- Cookie Protection
- Session Timeout
- Threat Logging
- Automatic Temporary File Deletion
- Security Dashboard
- Incident Reporting

# 📈 Dashboard

CyberShield provides a real-time security dashboard displaying:

- Registered Users
- Threats Detected
- Files Protected
- Files Recovered
- Security Reports Generated
- Recent Security Activity

# 🛡 Privacy

CyberShield is designed with user privacy in mind.

- Temporary uploaded files are automatically removed after processing.
- Encrypted backups remain protected until the user chooses to delete them.
- Passwords are securely hashed.
- Session cookies follow secure configuration.
- User data is never intentionally shared with third parties.

# ⚠ Disclaimer

CyberShield is an educational cybersecurity project developed for learning and demonstration purposes.

It simulates cybersecurity concepts such as ransomware recovery, cookie protection, and UPI fraud detection in a controlled environment. It is **not intended to replace commercial antivirus or enterprise cybersecurity solutions.**

# 👩‍💻 Developer

**Poeace Dhurandhar**

MCA Student | Python Developer | Cybersecurity Enthusiast

GitHub: https://github.com/Poeace

LinkedIn: https://www.linkedin.com/in/poeace-dhurandhar

