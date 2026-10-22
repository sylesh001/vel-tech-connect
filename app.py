import os
import sqlite3
import secrets
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import parseaddr
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")
DB_PATH = os.path.join(os.path.dirname(__file__), "college.db")
DEFAULT_ANNOUNCEMENT_EMAIL_PRIORITIES = {"Important", "Urgent"}
VALID_ANNOUNCEMENT_PRIORITIES = {"Normal", "Important", "Urgent"}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Replace these sample details with your college's verified information.
VELTECH_FAQS = [
    ("courses", "What courses are available?", "Vel Tech offers programmes across Engineering and Technology, Management, Law, Commerce, Media Technology and Communication, Science and Humanities, and research. Listed computing programmes include Artificial Intelligence and Data Science, AI and Machine Learning, Computer Science and Engineering, CSE specialisations, Computer Science and Design, and Information Technology. Other listed programmes include Aeronautical, Civil, Mechanical, Electrical and Electronics, Electronics and Communication, Biomedical Engineering, and Biotechnology. For the latest programme list, visit https://www.veltech.edu.in/admissions/ and https://www.veltech.edu.in/ ."),
    ("admission", "How can I apply for admission?", "Apply through Vel Tech's official online application portal: https://application.veltech.edu.in/ . Admissions and eligibility can differ by programme and intake. For B.Tech admission information, see https://www.veltech.edu.in/btech-admissions/ . The official B.Tech page currently lists 2027 eligibility information; check the page for the latest updates."),
    ("eligibility", "What is the B.Tech admission eligibility?", "Vel Tech's B.Tech admissions page for the 2027 intake states that applicants should have completed or be appearing for a recognised 10+2 or equivalent examination and lists a minimum of 60% in MPC (Mathematics, Physics and Chemistry). Eligibility can vary by route and applicable rules, so verify the latest criteria at https://www.veltech.edu.in/btech-admissions/ ."),
    ("fees", "What is the fee structure?", "B.Tech fees depend on the admission phase and applicable scholarship. Please use the official fee structure page for the current programme and intake: https://www.veltech.edu.in/fee-structure/ . Confirm the final amount with the admissions office before making a payment."),
    ("scholarship", "Are scholarships available?", "Yes. Vel Tech lists the Mahatma Gandhi National Merit Scholarship. Its official scholarship page describes tuition-fee concessions based on MPC aggregate and VTUEEE rank, subject to eligibility. The page lists 10% for 70–79.9%, 25% for 80–89.9%, 50% for 90–94.9%, and 75% above 95%; it also describes a 100% tuition-fee scholarship for the MPC topper from each State/Union Territory among admitted candidates. Check current eligibility and terms at https://www.veltech.edu.in/veltech-mahatma-gandhi-national-merit-scholarship/ ."),
    ("contact", "How do I contact the college office?", "Campus address: No. 42, Avadi–Vel Tech Road, Vel Nagar, Avadi, Chennai – 600 062, Tamil Nadu, India. Campus phone: 044-61710244. Admission contact numbers listed on the application portal: Tamil Nadu +91 94455 68802; Andhra Pradesh & Telangana +91 90031 07000; other states +91 74488 88954; toll-free 1800 212 7669. Admission email: admission@veltech.edu.in. Official contact page: https://www.veltech.edu.in/contact/ ."),
    ("address", "Where is Vel Tech located?", "Vel Tech's campus is at No. 42, Avadi–Vel Tech Road, Vel Nagar, Avadi, Chennai – 600 062, Tamil Nadu, India. See https://www.veltech.edu.in/contact/ for official contact details."),
    ("library", "What are the library timings?", "The official Central Library page lists working hours as 7:30 AM to 8:00 PM, including Saturdays and Sundays, except public holidays. It lists borrowing privileges of 6 books for 14 days for UG students and 6 books for 28 days for PG students. Check https://www.veltech.edu.in/central-library/ for rules and updates."),
    ("hostel", "Is hostel accommodation available?", "Yes. Vel Tech's official hostels page describes separate hostels for boys and girls and facilities including Wi-Fi, reading halls, dining, gymnasium, and security. Hostel availability, rules, contacts, and current tariffs are published at https://www.veltech.edu.in/hostels/ and https://www.veltech.edu.in/fee-structure/ . Please confirm current room availability and fees with the hostel office."),
    ("hostelfees", "What is the hostel fee at Vel Tech?", "Hostel charges depend on room type and the applicable academic year. Please check the official fee structure page for the current hostel tariff: https://www.veltech.edu.in/fee-structure/ . The page may show a previous academic-year table, so confirm the latest amount with the hostel office before payment."),
    ("transport", "Is college transport available?", "Yes. Vel Tech says its bus network serves locations across Chennai and surrounding areas. Routes, boarding points, booking, and current details are managed through the university's Transport Management System. Visit https://www.veltech.edu.in/transport/ for the official transport information; check the system or transport office for your route and fee."),
    ("documents", "What documents are required for admission?", "The required documents depend on the programme and admission route. The online application instructions mention keeping a scanned colour passport-size photograph and signature ready; academic certificates and other supporting documents may also be required. Follow the current checklist in the official application portal at https://application.veltech.edu.in/ and programme page before submitting."),
    ("timings", "What are the college working hours?", "Working hours can differ by department, academic timetable, and service. The Central Library's published hours are 7:30 AM to 8:00 PM except public holidays. For class timings or office hours, check the current timetable or contact the relevant department. Library details: https://www.veltech.edu.in/central-library/ ."),
    ("campus", "What facilities are available on campus?", "Vel Tech's official website lists facilities including hostels, library, transportation, laboratories, smart classrooms, seminar halls, auditoriums, sports facilities, medical centres, Wi-Fi, canteen/cafeteria, and placement/training support. See https://www.veltech.edu.in/infrastructure/ and https://www.veltech.edu.in/campus-life/ ."),
    ("placement", "Where can I find placement information?", "Vel Tech publishes placement and campus-to-corporate information on its official website. Please visit https://www.veltech.edu.in/placements/ for the latest details."),
    ("application", "Where is the online application form?", "Use Vel Tech's official online application portal: https://application.veltech.edu.in/ . Review the programme-specific eligibility and document checklist before applying."),
    ("complaint", "How do I submit a complaint in this portal?", "Log in with your student account, open Complaint Box, select a category, enter a subject and description, and submit. Save the complaint reference number. You can view the status and administrator response from your student dashboard."),
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _valid_email_address(address):
    if not isinstance(address, str) or not EMAIL_PATTERN.fullmatch(address):
        return False
    display_name, parsed_address = parseaddr(address)
    return not display_name and parsed_address == address

def _email_configuration():
    host = os.environ.get("SMTP_HOST", "").strip()
    sender = os.environ.get("SMTP_SENDER_EMAIL", "").strip()
    security = os.environ.get("SMTP_SECURITY", "starttls").strip().lower()
    username = os.environ.get("SMTP_USERNAME", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "")
    test_mode = os.environ.get("EMAIL_TEST_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
    test_recipient = os.environ.get("EMAIL_TEST_RECIPIENT", "").strip()

    if not host:
        return None, "SMTP_HOST is not configured"
    if not _valid_email_address(sender):
        return None, "SMTP_SENDER_EMAIL is missing or invalid"
    try:
        port = int(os.environ.get("SMTP_PORT", "587"))
    except ValueError:
        return None, "SMTP_PORT must be a number"
    if not 1 <= port <= 65535:
        return None, "SMTP_PORT must be between 1 and 65535"
    if security not in {"starttls", "ssl", "none"}:
        return None, "SMTP_SECURITY must be starttls, ssl, or none"
    if bool(username) != bool(password):
        return None, "SMTP_USERNAME and SMTP_PASSWORD must either both be set or both be empty"
    if test_mode and not _valid_email_address(test_recipient):
        return None, "EMAIL_TEST_RECIPIENT must be a valid address when EMAIL_TEST_MODE is enabled"

    return {
        "host": host,
        "port": port,
        "sender": sender,
        "security": security,
        "username": username,
        "password": password,
        "test_mode": test_mode,
        "test_recipient": test_recipient,
    }, None

def _send_email(recipient, subject, body, configuration):
    if not _valid_email_address(recipient):
        app.logger.warning("Email notification skipped because a recipient address is invalid")
        return False

    message = EmailMessage()
    message["Subject"] = " ".join(subject.splitlines())
    message["From"] = configuration["sender"]
    message["To"] = recipient
    message.set_content(body)

    try:
        if configuration["security"] == "ssl":
            connection = smtplib.SMTP_SSL(
                configuration["host"],
                configuration["port"],
                timeout=15,
                context=ssl.create_default_context(),
            )
        else:
            connection = smtplib.SMTP(
                configuration["host"],
                configuration["port"],
                timeout=15,
            )
        with connection as server:
            if configuration["security"] == "starttls":
                server.starttls(context=ssl.create_default_context())
            if configuration["username"]:
                server.login(configuration["username"], configuration["password"])
            server.send_message(message)
        app.logger.info("Email message was accepted by the SMTP server")
        return True
    except (OSError, smtplib.SMTPException, ValueError):
        app.logger.exception("Email notification delivery failed")
        return False

def _send_student_notification(subject, body):
    configuration, config_error = _email_configuration()
    if configuration is None:
        app.logger.warning("Email notification skipped: %s", config_error)
        return "disabled"

    if configuration["test_mode"]:
        recipients = [configuration["test_recipient"]]
        app.logger.info("Email test mode is active; student notification redirected to the test recipient")
    else:
        with get_db() as db:
            addresses = db.execute(
                "SELECT email FROM users WHERE role = 'student' ORDER BY id"
            ).fetchall()
        db.close()
        recipients = []
        seen = set()
        for row in addresses:
            address = row["email"].strip()
            normalized = address.casefold()
            if _valid_email_address(address) and normalized not in seen:
                recipients.append(address)
                seen.add(normalized)
        if not recipients:
            app.logger.warning("Email notification skipped because there are no valid student email addresses")
            return "no_recipients"

    delivered = 0
    for recipient in recipients:
        if _send_email(recipient, subject, body, configuration):
            delivered += 1
    if delivered == len(recipients):
        return "sent"
    return "partial" if delivered else "failed"

def _send_complaint_notification(recipient, subject, body):
    configuration, config_error = _email_configuration()
    if configuration is None:
        app.logger.warning("Email notification skipped: %s", config_error)
        return "disabled"
    if not _valid_email_address(recipient):
        app.logger.warning("Complaint email notification skipped because the student's email address is invalid")
        return "no_recipients"

    target = recipient
    if configuration["test_mode"]:
        target = configuration["test_recipient"]
        app.logger.info("Email test mode is active; complaint notification redirected to the test recipient")
    return "sent" if _send_email(target, subject, body, configuration) else "failed"

def _announcement_email_priorities():
    configured = os.environ.get(
        "ANNOUNCEMENT_EMAIL_PRIORITIES",
        ",".join(sorted(DEFAULT_ANNOUNCEMENT_EMAIL_PRIORITIES)),
    )
    priorities = {value.strip().title() for value in configured.split(",") if value.strip()}
    invalid = priorities - VALID_ANNOUNCEMENT_PRIORITIES
    if invalid:
        app.logger.warning("Ignoring invalid values in ANNOUNCEMENT_EMAIL_PRIORITIES")
    return priorities & VALID_ANNOUNCEMENT_PRIORITIES

def _notification_feedback(result, event_name):
    if result == "disabled":
        flash(
            f"{event_name} saved, but email notifications are disabled. Configure SMTP settings to enable them.",
            "warning",
        )
    elif result == "failed":
        flash(f"{event_name} saved, but email notification failed. Check the server log.", "warning")
    elif result == "partial":
        flash(f"{event_name} saved, but some email notifications failed. Check the server log.", "warning")
    elif result == "no_recipients":
        flash(f"{event_name} saved, but there are no valid student email addresses.", "warning")

def _complaint_notification_body(complaint, status, response, response_changed):
    lines = [
        "Your complaint has been updated.",
        "",
        f"Reference: {complaint['complaint_code']}",
        f"Subject: {complaint['subject']}",
        f"Status: {status}",
    ]
    if response_changed:
        lines.extend(["", "Administrator response:"])
        lines.append(response if response else "The previous response was removed.")
    lines.extend(["", "This is an automated notification from Vel Tech Connect."])
    return "\n".join(lines)

def _announcement_notification_body(announcement, published_at):
    return "\n".join([
        "A new college announcement has been published.",
        "",
        f"Title: {announcement['title']}",
        f"Priority: {announcement['priority']}",
        f"Published: {published_at}",
        "",
        announcement["message"],
        "",
        "This is an automated notification from Vel Tech Connect.",
    ])

def _log_email_configuration():
    configuration, config_error = _email_configuration()
    if configuration is None:
        app.logger.warning("Email notifications are disabled: %s", config_error)
    elif configuration["test_mode"]:
        app.logger.warning("Email test mode is enabled; notifications will go only to the configured test recipient")
    elif configuration["security"] == "none":
        app.logger.warning("SMTP transport security is disabled; use STARTTLS or SSL outside local testing")

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_code TEXT NOT NULL UNIQUE,
            student_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            admin_response TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'Normal'
                CHECK (priority IN ('Normal', 'Important', 'Urgent')),
            published INTEGER NOT NULL DEFAULT 0 CHECK (published IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            published_at TEXT
        );
        """)
        # Upsert the official Vel Tech FAQ set by question. This updates starter FAQ
        # answers in an existing college.db and adds new questions without deleting
        # any extra FAQs that an administrator has added.
        for topic, question, answer in VELTECH_FAQS:
            existing = db.execute("SELECT id FROM faqs WHERE question = ?", (question,)).fetchone()
            if existing:
                db.execute("UPDATE faqs SET topic = ?, answer = ? WHERE id = ?", (topic, answer, existing["id"]))
            else:
                db.execute("INSERT INTO faqs(topic, question, answer) VALUES (?, ?, ?)", (topic, question, answer))
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@college.local")
        admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@123")
        admin = db.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
        if not admin:
            db.execute(
                "INSERT INTO users(name, email, password_hash, role, created_at) VALUES (?, ?, ?, 'admin', ?)",
                ("College Administrator", admin_email, generate_password_hash(admin_password), datetime.now().isoformat(timespec="seconds"))
            )

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in as an administrator.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    if session.get("user_id"):
        return redirect(url_for("student_dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email, and a password with at least 8 characters.", "danger")
            return render_template("register.html")
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users(name, email, password_hash, role, created_at) VALUES (?, ?, ?, 'student', ?)",
                    (name, email, generate_password_hash(password), datetime.now().isoformat(timespec="seconds"))
                )
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("student_dashboard"))
        flash("Incorrect email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/student")
@login_required
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("admin_dashboard"))
    with get_db() as db:
        complaints = db.execute(
            "SELECT * FROM complaints WHERE student_id = ? ORDER BY id DESC",
            (session["user_id"],)
        ).fetchall()
        announcements = db.execute(
            """SELECT * FROM announcements WHERE published = 1
               ORDER BY published_at DESC, id DESC"""
        ).fetchall()
    return render_template("student.html", complaints=complaints, announcements=announcements)

@app.route("/chat")
@login_required
def chat_page():
    if session.get("role") != "student":
        return redirect(url_for("admin_dashboard"))
    return render_template("chat.html")

@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    if session.get("role") != "student":
        return {"answer": "Only students can use the enquiry chatbot."}, 403
    data = request.get_json(silent=True) or {}
    question = str(data.get("message", "")).strip().lower()
    if not question:
        return {"answer": "Please type a college-related question."}, 400
    with get_db() as db:
        faqs = db.execute("SELECT topic, question, answer FROM faqs").fetchall()
    # Lightweight keyword matching over college FAQ records.
    tokens = set(question.replace("?", " ").replace(",", " ").replace(".", " ").split())
    best, best_score = None, 0
    for faq in faqs:
        keywords = set((faq["topic"] + " " + faq["question"]).lower().replace("?", " ").replace("–", " ").replace("-", " ").split())
        score = len(tokens & keywords)
        # Add helpful topic synonyms.
        synonyms = {
            "fees": {"fee", "fees", "cost", "payment", "tuition", "amount", "price"},
            "admission": {"admission", "apply", "application", "join", "eligibility", "intake"},
            "eligibility": {"eligibility", "eligible", "percentage", "marks", "criteria", "qualification"},
            "courses": {"course", "courses", "department", "degree", "program", "programme", "branch", "branches", "study"},
            "hostel": {"hostel", "hostels", "accommodation", "room", "residence", "stay"},
            "hostelfees": {"hostel", "hostels", "fee", "fees", "room", "tariff", "cost"},
            "transport": {"bus", "transport", "route", "routes", "boarding", "pickup"},
            "library": {"library", "book", "books", "borrow", "timings"},
            "timings": {"time", "timing", "hours", "open", "working", "schedule", "class"},
            "scholarship": {"scholarship", "financial", "aid", "merit", "concession", "waiver"},
            "documents": {"document", "documents", "certificate", "mark", "marks", "photo", "signature", "checklist"},
            "contact": {"contact", "phone", "email", "office", "address", "number", "call"},
            "address": {"location", "where", "address", "campus", "located"},
            "campus": {"facility", "facilities", "campus", "canteen", "laboratory", "labs", "wifi", "sports"},
            "placement": {"placement", "placements", "job", "jobs", "career", "recruiter"},
            "application": {"form", "apply", "application", "portal", "online"},
            "complaint": {"complaint", "complaints", "report", "issue", "reference", "status"}
        }
        if faq["topic"] in synonyms:
            score += len(tokens & synonyms[faq["topic"]]) * 2
        if score > best_score:
            best, best_score = faq, score
    if best and best_score > 0:
        answer = best["answer"]
    else:
        answer = "I couldn't find a reliable answer in the college enquiry information. Please try asking about courses, admissions, fees, scholarships, hostel, transport, library, timings, documents, or contact details."
    return {"answer": answer}

@app.route("/complaints/new", methods=["GET", "POST"])
@login_required
def new_complaint():
    if session.get("role") != "student":
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        allowed = {"Classroom", "Laboratory", "Library", "Hostel", "Transport", "Canteen", "Cleanliness", "Other"}
        if category not in allowed or not subject or not description:
            flash("Please complete every field with valid information.", "danger")
            return render_template("complaint_new.html")
        code = "CMP-" + secrets.token_hex(4).upper()
        now = datetime.now().isoformat(timespec="seconds")
        with get_db() as db:
            db.execute(
                """INSERT INTO complaints(complaint_code, student_id, category, subject, description, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 'Pending', ?, ?)""",
                (code, session["user_id"], category, subject, description, now, now)
            )
        flash(f"Complaint submitted. Your reference number is {code}.", "success")
        return redirect(url_for("student_dashboard"))
    return render_template("complaint_new.html")

@app.route("/admin")
@admin_required
def admin_dashboard():
    with get_db() as db:
        complaints = db.execute(
            """SELECT complaints.*, users.name AS student_name, users.email AS student_email
               FROM complaints JOIN users ON users.id = complaints.student_id
               ORDER BY complaints.id DESC"""
        ).fetchall()
        status_counts = {"Pending": 0, "In Progress": 0, "Resolved": 0}
        for row in db.execute(
            "SELECT status, COUNT(*) AS count FROM complaints GROUP BY status ORDER BY status"
        ).fetchall():
            status_counts[row["status"]] = row["count"]
        counts = {
            "total": sum(status_counts.values()),
            "pending": status_counts["Pending"],
            "progress": status_counts["In Progress"],
            "resolved": status_counts["Resolved"],
        }
        category_counts = db.execute(
            "SELECT category, COUNT(*) AS count FROM complaints GROUP BY category ORDER BY category"
        ).fetchall()
        recent_complaints = db.execute(
            """SELECT complaint_code, subject, status, created_at
               FROM complaints ORDER BY id DESC LIMIT 10"""
        ).fetchall()
        announcements = db.execute(
            "SELECT * FROM announcements ORDER BY created_at DESC, id DESC"
        ).fetchall()
        faqs = db.execute("SELECT * FROM faqs ORDER BY topic").fetchall()
    return render_template(
        "admin.html",
        complaints=complaints,
        counts=counts,
        status_counts=status_counts,
        category_counts=category_counts,
        recent_complaints=recent_complaints,
        announcements=announcements,
        faqs=faqs,
    )

@app.route("/admin/announcements", methods=["POST"])
@admin_required
def create_announcement():
    title = request.form.get("title", "").strip()
    message = request.form.get("message", "").strip()
    priority = request.form.get("priority", "Normal").strip()
    published = request.form.get("published") == "1"
    if not title or len(title) > 120 or not message or len(message) > 5000:
        flash("Enter a title (up to 120 characters) and message (up to 5000 characters).", "danger")
        return redirect(url_for("admin_dashboard") + "#announcements")
    if priority not in {"Normal", "Important", "Urgent"}:
        flash("Choose a valid announcement priority.", "danger")
        return redirect(url_for("admin_dashboard") + "#announcements")

    now = datetime.now().isoformat(timespec="seconds")
    with get_db() as db:
        result = db.execute(
            """INSERT INTO announcements(title, message, priority, published, created_at, updated_at, published_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, message, priority, int(published), now, now, now if published else None)
        )
        announcement_id = result.lastrowid
    db.close()
    flash("Announcement created.", "success")
    if published and priority in _announcement_email_priorities():
        announcement = {"title": title, "message": message, "priority": priority}
        result = _send_student_notification(
            f"College announcement: {' '.join(title.splitlines())}",
            _announcement_notification_body(announcement, now),
        )
        _notification_feedback(result, "Announcement")
    return redirect(url_for("admin_dashboard") + "#announcements")

@app.route("/admin/announcements/<int:announcement_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_announcement(announcement_id):
    with get_db() as db:
        announcement = db.execute(
            "SELECT * FROM announcements WHERE id = ?", (announcement_id,)
        ).fetchone()
        if announcement is None:
            abort(404)
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            message = request.form.get("message", "").strip()
            priority = request.form.get("priority", "").strip()
            if not title or len(title) > 120 or not message or len(message) > 5000:
                flash("Enter a title (up to 120 characters) and message (up to 5000 characters).", "danger")
            elif priority not in {"Normal", "Important", "Urgent"}:
                flash("Choose a valid announcement priority.", "danger")
            else:
                db.execute(
                    """UPDATE announcements SET title = ?, message = ?, priority = ?, updated_at = ?
                       WHERE id = ?""",
                    (title, message, priority, datetime.now().isoformat(timespec="seconds"), announcement_id)
                )
                flash("Announcement updated.", "success")
                return redirect(url_for("admin_dashboard") + "#announcements")
    return render_template("announcement_edit.html", announcement=announcement)

@app.route("/admin/announcements/<int:announcement_id>/publication", methods=["POST"])
@admin_required
def set_announcement_publication(announcement_id):
    action = request.form.get("action", "")
    if action not in {"publish", "unpublish"}:
        abort(400)
    published = action == "publish"
    now = datetime.now().isoformat(timespec="seconds")
    with get_db() as db:
        announcement = db.execute(
            "SELECT title, message, priority, published FROM announcements WHERE id = ?",
            (announcement_id,),
        ).fetchone()
        if announcement is None:
            abort(404)
        should_notify = (
            published
            and not announcement["published"]
            and announcement["priority"] in _announcement_email_priorities()
        )
        result = db.execute(
            """UPDATE announcements
               SET published = ?, updated_at = ?,
                   published_at = CASE WHEN ? = 1 THEN ? ELSE published_at END
               WHERE id = ?""",
            (int(published), now, int(published), now, announcement_id)
        )
    db.close()
    flash("Announcement published." if published else "Announcement unpublished.", "success")
    if should_notify:
        notification = {
            "title": announcement["title"],
            "message": announcement["message"],
            "priority": announcement["priority"],
        }
        result = _send_student_notification(
            f"College announcement: {' '.join(announcement['title'].splitlines())}",
            _announcement_notification_body(notification, now),
        )
        _notification_feedback(result, "Announcement")
    return redirect(url_for("admin_dashboard") + "#announcements")

@app.route("/admin/announcements/<int:announcement_id>/delete", methods=["POST"])
@admin_required
def delete_announcement(announcement_id):
    with get_db() as db:
        result = db.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
        if result.rowcount == 0:
            abort(404)
    flash("Announcement deleted.", "success")
    return redirect(url_for("admin_dashboard") + "#announcements")

@app.route("/admin/complaint/<int:complaint_id>", methods=["POST"])
@admin_required
def update_complaint(complaint_id):
    status = request.form.get("status", "")
    response = request.form.get("admin_response", "").strip()
    if status not in {"Pending", "In Progress", "Resolved"}:
        abort(400)
    with get_db() as db:
        complaint = db.execute(
            """SELECT complaints.complaint_code, complaints.subject, complaints.status,
                      complaints.admin_response, users.email
               FROM complaints JOIN users ON users.id = complaints.student_id
               WHERE complaints.id = ?""",
            (complaint_id,),
        ).fetchone()
        if complaint is None:
            abort(404)
        response_changed = response != (complaint["admin_response"] or "")
        changed = status != complaint["status"] or response_changed
        if changed:
            db.execute(
                "UPDATE complaints SET status = ?, admin_response = ?, updated_at = ? WHERE id = ?",
                (status, response, datetime.now().isoformat(timespec="seconds"), complaint_id)
            )
    db.close()
    flash("Complaint updated.", "success")
    if changed:
        notification = {
            "complaint_code": complaint["complaint_code"],
            "subject": complaint["subject"],
        }
        body = _complaint_notification_body(notification, status, response, response_changed)
        result = _send_complaint_notification(
            complaint["email"],
            f"Complaint update: {complaint['complaint_code']}",
            body,
        )
        _notification_feedback(result, "Complaint update")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/faq", methods=["POST"])
@admin_required
def add_faq():
    topic = request.form.get("topic", "").strip().lower()
    question = request.form.get("question", "").strip()
    answer = request.form.get("answer", "").strip()
    if not topic or not question or not answer:
        flash("Complete all FAQ fields.", "danger")
    else:
        with get_db() as db:
            db.execute("INSERT INTO faqs(topic, question, answer) VALUES (?, ?, ?)", (topic, question, answer))
        flash("College enquiry information added.", "success")
    return redirect(url_for("admin_dashboard") + "#faqs")

@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, message="You do not have permission to view this page."), 403

@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="The page you requested was not found."), 404

_log_email_configuration()
init_db()

if __name__ == "__main__":
    app.run(debug=True)
