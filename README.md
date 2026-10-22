# Vel Tech Connect — College Enquiry Chatbot + Complaint Box

## Requirements
- Python 3.10+
- VS Code (recommended)

## Run on Windows
1. Extract this ZIP.
2. Open the extracted `college_enquiry_chatbot` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:
   `py -m venv .venv`
5. Activate it in PowerShell:
   `.\.venv\Scripts\Activate.ps1`
   If PowerShell blocks activation, use Command Prompt:
   `.venv\Scripts\activate.bat`
6. Install Flask:
   `python -m pip install -r requirements.txt`
7. Run:
   `python app.py`
8. Open `http://127.0.0.1:5000` in your browser.

## Local admin demo login
- Email: `admin@college.local`
- Password: `Admin@123`

Change the demo admin password and secret key before deployment. This demo uses a local SQLite database (`college.db`) created automatically.

## Features
- Student registration and login
- College enquiry chatbot using keyword/question matching against saved FAQ entries
- Student complaint submission with reference number
- Students see only their own complaints
- Admin-only complaint list, status changes, and responses
- Admin analytics dashboard with live complaint counts, status and category charts, and recent submissions
- Admin announcements management with priorities, editing, publication controls, and student-visible updates
- Optional SMTP email notifications for complaint updates and important/urgent announcements
- Admin can add FAQ information for the chatbot

## Email notifications

Email notifications are optional and use Python's built-in SMTP and email libraries; no additional package is required. If SMTP is not configured, the app starts normally, logs a warning, and saves complaint and announcement changes without sending email.

Set the following environment variables in the same PowerShell terminal before running `python app.py`:

```powershell
$env:SMTP_HOST = "smtp.example.com"
$env:SMTP_PORT = "587"
$env:SMTP_SECURITY = "starttls"
$env:SMTP_SENDER_EMAIL = "portal@example.com"
$env:SMTP_USERNAME = "portal@example.com"
$env:SMTP_PASSWORD = "your-provider-app-password"
$env:EMAIL_TEST_MODE = "true"
$env:EMAIL_TEST_RECIPIENT = "your-own-test-inbox@example.com"
$env:ANNOUNCEMENT_EMAIL_PRIORITIES = "Important,Urgent"
python app.py
```

Replace the example values with settings from your email provider. Use an app password if your provider requires one; do not paste credentials into chat, add them to source code, or commit them. These PowerShell values last only for that terminal session. For persistent configuration, use Windows Environment Variables instead.

`SMTP_SECURITY` supports `starttls` (recommended for port 587), `ssl` (commonly port 465), or `none` only for a trusted local SMTP relay. SMTP username and password must either both be configured or both omitted.

Keep `EMAIL_TEST_MODE` set to `true` while testing. In this mode, notifications are redirected to the single `EMAIL_TEST_RECIPIENT` address instead of going to students. The app logs that test mode is active. After verifying the messages, set `EMAIL_TEST_MODE` to `false` before allowing real student notifications. The default announcement notification priorities are `Important,Urgent`; change `ANNOUNCEMENT_EMAIL_PRIORITIES` to include `Normal` if normal announcements should also send emails.

For a safe test, publish an Important announcement and change a test complaint's status while test mode is enabled. Confirm that only the test inbox receives the messages. Saving an unchanged complaint or publishing an already-published announcement does not send another message. SMTP errors are recorded in the server log; they do not roll back the database update. An SMTP server accepting a message does not guarantee final delivery to an inbox.

The project has no `.gitignore` or `.env` loader, and this setup uses environment variables directly, so no `.env` file is needed or created.

## Vel Tech information
The app includes FAQs based on public information on the official Vel Tech website: https://www.veltech.edu.in/ . The app updates its built-in FAQ answers when it starts, including when an existing `college.db` is present, while preserving additional FAQs added by the administrator. Fees, admission criteria, scholarship rules, hostel charges, and routes can change; the chatbot links to the official page and advises students to confirm current details.

Key official sources: admissions (https://www.veltech.edu.in/admissions/), B.Tech admission (https://www.veltech.edu.in/btech-admissions/), fees (https://www.veltech.edu.in/fee-structure/), scholarships (https://www.veltech.edu.in/veltech-mahatma-gandhi-national-merit-scholarship/), library (https://www.veltech.edu.in/central-library/), hostels (https://www.veltech.edu.in/hostels/), transport (https://www.veltech.edu.in/transport/), contact (https://www.veltech.edu.in/contact/).

To reset all demo data, stop the app and delete `college.db`; it will be recreated on next run. Existing users and complaints remain in the database if you simply replace `app.py` with this updated version.

## Notes
- This is a one-day academic project starter, not a production-ready deployment.
- For real deployment, set a strong random `SECRET_KEY`, change admin credentials, enable HTTPS, add CSRF protection and rate limiting, and configure backups.
- The chatbot is a basic NLP-style keyword matcher, not a large language model. Describe it accurately in your report.
