# UPI Fraud Detection Enhancement - Testing Guide

## Pre-Deployment Setup

### 1. Database Migration
```bash
cd /path/to/cyber
python migrate_upi_reports.py
```

Expected output:
```
✅ SUCCESS: UPI Fraud Reports table created successfully!

Table Details:
  Table Name: upi_fraud_reports
  Columns: id, report_id, user_id, user_email, upi_handle, threat_level, risk_score, detection_result, submission_date, cyber_team_notified, user_confirmation_sent, status
```

### 2. Verify Email Configuration
Check `app/config.py` or environment variables for:
```python
MAIL_SERVER = "smtp.gmail.com"  # or your SMTP server
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "your-email@gmail.com"
MAIL_PASSWORD = "your-app-password"
MAIL_DEFAULT_SENDER = "cybershield-team@example.com"
```

---

## Manual Testing Scenarios

### Scenario 1: Submit UPI Fraud Report

#### Steps:
1. Navigate to `/module/upifraud`
2. Enter a UPI ID (e.g., `test@ybl` or `suspicious@paytm`)
3. Click "Analyze"
4. Review the fraud assessment result
5. Click "Report to Cyber Team" button
6. Observe success message with Report ID

#### Expected Outcomes:
- ✅ Success message displays with Report ID (format: UFR-XXXXXXXXXXXX)
- ✅ Database entry created in `upi_fraud_reports` table
- ✅ Email sent to cyber team (check email logs or test mailbox)
- ✅ Confirmation email sent to user's registered email
- ✅ Both `cyber_team_notified` and `user_confirmation_sent` flags set to True

#### Verification Steps:
```sql
SELECT * FROM upi_fraud_reports 
ORDER BY submission_date DESC 
LIMIT 1;
```

Check fields:
- `report_id`: Not NULL, starts with "UFR-"
- `user_id`: Matches logged-in user
- `user_email`: User's registered email
- `upi_handle`: Value entered
- `threat_level`: High Risk / Medium Risk / Safe
- `risk_score`: 0-100
- `submission_date`: Current timestamp
- `cyber_team_notified`: 1 (TRUE)
- `user_confirmation_sent`: 1 (TRUE)
- `status`: 'pending'

---

### Scenario 2: View My Reports

#### Steps:
1. After submitting report(s) in Scenario 1
2. Navigate to `/upi/my-reports`
3. Review the reports dashboard

#### Expected Outcomes:
- ✅ Summary cards show correct counts
  - Total Reports: > 0
  - Pending Review: matches status='pending' count
  - Under Investigation: matches status='under_review' count
  - Resolved: matches status='resolved' count
  
- ✅ Reports table/cards display:
  - Report ID (UFR-XXXX...)
  - UPI Handle
  - Threat Level (with colored badge)
  - Risk Score with color coding
  - Status with appropriate badge
  - Submission date/time
  
- ✅ View button opens detailed modal with:
  - Full report information
  - Detection results formatted as bullet list
  - Notification status (checkmarks or pending)
  - Important warning message
  - Close button

#### Mobile Testing:
- Reports display in card format (not table)
- All information readable on small screens
- Buttons fully functional on touch devices
- Modal responsive and scrollable

---

### Scenario 3: Email Content Verification

#### Cyber Team Email Test:
1. Submit report via `/module/upifraud`
2. Check cyber team mailbox (MAIL_DEFAULT_SENDER address)

**Expected Email Content:**
```
Subject: [CyberShield Alert] UPI Fraud Report - test@ybl

Body should contain:
- Reported by: [User Full Name] (username)
- Email: user@example.com
- UPI Handle: test@ybl
- Risk Score: XX/100
- Threat Level: [Status]
- Detection Results: [Formatted reasons]
- Report ID: cyber_report.id
- Fraud Report ID: UFR-XXXX...
- Reported at: YYYY-MM-DD HH:MM:SS
- Investigation instructions
```

#### User Confirmation Email Test:
1. Submit report via `/module/upifraud`
2. Check user's registered email

**Expected Email Content:**
```
Subject: CyberShield Fraud Report Confirmation

Body should contain:
- Dear [User Full Name]
- Thank you message
- REPORT DETAILS section:
  - Report ID: UFR-XXXX...
  - Suspicious UPI ID: test@ybl
  - Threat Status: [Status]
  - Risk Score: XX/100
  - Submission Date & Time: YYYY-MM-DD HH:MM:SS
- DETECTION RESULTS section:
  - Formatted bullet list
- NEXT STEPS section:
  - 24-hour review timeline
- TRACK YOUR REPORT section:
  - Link to My Reports page
- Important warning about UPI usage
- Support contact information
```

---

### Scenario 4: Multiple Reports from Same User

#### Steps:
1. Submit 3-4 UPI fraud reports
2. Navigate to `/upi/my-reports`

#### Expected Outcomes:
- ✅ All reports display in list
- ✅ Reports ordered by newest first
- ✅ Each report has unique Report ID
- ✅ Summary counts reflect all reports
- ✅ All modals work correctly

---

### Scenario 5: Error Handling

#### Test Email Failure:
1. Temporarily disable email service
2. Submit UPI fraud report
3. Observe error handling

**Expected Outcomes:**
- ✅ Error message displayed to user
- ✅ Database entry still created (partial success)
- ✅ Application doesn't crash
- ✅ Logs contain warning message

#### Test Database Failure:
1. Temporarily disable database
2. Submit UPI fraud report
3. Observe error handling

**Expected Outcomes:**
- ✅ User sees error message
- ✅ Email not sent (due to transaction rollback)
- ✅ No partial database entry created
- ✅ Logs contain error details

---

## Automated Test Cases

### Unit Tests for Report Generation
```python
def test_generate_report_id():
    """Test unique report ID generation"""
    from uuid import uuid4
    report_id = f"UFR-{uuid4().hex[:12].upper()}"
    assert report_id.startswith("UFR-")
    assert len(report_id) == 16  # UFR- + 12 chars

def test_upi_fraud_report_creation():
    """Test UPIFraudReport model creation"""
    from app.models import UPIFraudReport
    from datetime import datetime
    
    report = UPIFraudReport(
        report_id="UFR-TEST123456",
        user_id=1,
        user_email="test@example.com",
        upi_handle="test@ybl",
        threat_level="High Risk",
        risk_score=85,
        detection_result="Multiple fraud indicators detected",
    )
    
    assert report.report_id == "UFR-TEST123456"
    assert report.user_id == 1
    assert report.status == "pending"
    assert report.cyber_team_notified == False
    assert report.user_confirmation_sent == False
```

### Integration Tests
```python
def test_cyber_report_flow():
    """Test complete cyber report submission flow"""
    with client:
        # Login user
        client.post('/auth/login', data={...})
        
        # Submit report
        response = client.post('/module/upifraud', data={
            'upi_id': 'test@ybl',
            'cyber_report': '1'
        })
        
        # Verify response
        assert response.status_code == 200
        assert b'Report #UFR-' in response.data
        
        # Verify database
        report = UPIFraudReport.query.filter_by(
            upi_handle='test@ybl'
        ).first()
        assert report is not None
        assert report.user_id == current_user.user_id

def test_view_reports():
    """Test viewing user's reports"""
    with client:
        # Login user
        client.post('/auth/login', data={...})
        
        # View reports
        response = client.get('/upi/my-reports')
        
        # Verify response
        assert response.status_code == 200
        assert b'My UPI Fraud Reports' in response.data
```

---

## Performance Testing

### Load Test: Multiple Concurrent Reports
```bash
# Test 10 concurrent report submissions
ab -n 10 -c 10 -p data.txt -T application/x-www-form-urlencoded \
   http://localhost:5000/module/upifraud
```

**Expected Outcomes:**
- ✅ All requests succeed
- ✅ Each creates unique report_id
- ✅ Database handles concurrent writes
- ✅ No duplicate report IDs

### Database Query Performance
```sql
-- Check index on report_id
EXPLAIN QUERY PLAN 
SELECT * FROM upi_fraud_reports WHERE report_id = 'UFR-XXXX...';

-- Should use index efficiently
```

---

## Security Testing

### Test 1: Authorization
```python
# User A submits report
user_a_report = UPIFraudReport.create(...)

# Login as User B
login_as(user_b)

# Try to access User A's report details
response = get('/upi/my-reports')

# Verify User A's reports don't appear
assert user_a_report.report_id not in response.data
```

### Test 2: XSS Prevention
1. Submit report with UPI ID containing: `<script>alert('xss')</script>@ybl`
2. Navigate to `/upi/my-reports`
3. Verify script doesn't execute (should be escaped in HTML)

### Test 3: CSRF Protection
1. Ensure CSRF token required on form
2. Try to submit without CSRF token
3. Verify request rejected

---

## Regression Testing

### Existing Features:
- [ ] Basic UPI validation still works
- [ ] Risk scoring unchanged
- [ ] QR code reading functional
- [ ] Local report functionality (Report this UPI button)
- [ ] UPI scan history recording
- [ ] All existing pages load correctly
- [ ] Authentication and login work
- [ ] User dashboard displays correctly

---

## Deployment Checklist

Before going to production:

- [ ] Run database migration
- [ ] Verify email configuration
- [ ] Run all manual test scenarios
- [ ] Run automated tests (if applicable)
- [ ] Performance test load handling
- [ ] Security test authorization
- [ ] Test error handling paths
- [ ] Verify logging is working
- [ ] Check database backups
- [ ] Verify SSL/TLS for email
- [ ] Document admin procedures
- [ ] Train support team

---

## Troubleshooting

### Issue: Emails not being sent
**Solution:**
1. Verify MAIL_SERVER and MAIL_PORT config
2. Check MAIL_USERNAME and MAIL_PASSWORD
3. Review Flask-Mail logs
4. Test SMTP connection manually
5. Check email provider spam folder

### Issue: Reports not appearing in "My Reports"
**Solution:**
1. Verify database migration ran successfully
2. Check user_id foreign key relationship
3. Verify UPIFraudReport model imported correctly
4. Check application logs for exceptions

### Issue: Report ID format incorrect
**Solution:**
1. Verify uuid module imported
2. Check report_id generation: `f"UFR-{uuid.uuid4().hex[:12].upper()}"`
3. Ensure no whitespace in format

### Issue: Modal not opening
**Solution:**
1. Verify Bootstrap CSS/JS loaded
2. Check modal target ID matches button data-bs-target
3. Verify report data passed correctly to template

---

## Test Data

### Test UPI IDs:
- `test@ybl` - Should validate (known provider)
- `suspicious@paytm` - Should validate
- `fraud@okaxis` - Should validate
- `invalid@unknown` - Should fail validation

### Test Risk Scenarios:
- Single report: Low-Medium risk
- Multiple reports: Medium-High risk
- Unknown provider: Invalid

---

## Support Resources

- Flask-Mail Documentation: https://pythonhosted.org/Flask-Mail/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/
- Jinja2 Templates: https://jinja.palletsprojects.com/
- Bootstrap 5: https://getbootstrap.com/docs/5.0/

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| QA Lead | | | |
| DevOps | | | |
| Product Owner | | | |
