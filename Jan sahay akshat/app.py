"""
JANSAHAY: AI-DRIVEN WELFARE & GRIEVANCE INFRASTRUCTURE
Lead Architect: Akshat Gaur | B.Tech CSE (4th Year)
Architecture: Multi-Model Neural Pipeline (NLP + Random Forest)
"""

import os, random, sqlite3, joblib, smtplib, logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
import numpy as np

app = Flask(__name__)
app.secret_key = 'akshat_gaur_mckinsey_standard_2026'

# --- INFRASTRUCTURE CONFIGURATION ---
CONFIG = {
    "MAIL_USER": "YOUR EMAIL",
    "MAIL_PASS": "EMAIL APP PASSWORD", 
    "DB": "jansahay.db",
    "GRIEVANCE_MODEL": "models/jan_sahay_model.pkl",
    "WELFARE_MODEL": "models/welfare_model.pkl"
}

# --- KERNEL SYNCHRONIZATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JanSahay_Core")

try:
    # Model 1: Grievance classification
    grievance_engine = joblib.load(CONFIG["GRIEVANCE_MODEL"])
    # Model 2: Welfare prediction
    welfare_engine = joblib.load(CONFIG["WELFARE_MODEL"])
    logger.info("Multi-Model Intelligence Synchronized.")
except Exception as e:
    logger.error(f"Sync Failure: {e}")
    grievance_engine = welfare_engine = None

# Welfare Mapping Dataset
SCHEME_MAP = {
    0: {"name": "PM Awas Yojana", "desc": "Housing subsidy for low-income demographics.", "benefits": "₹2.67 Lakh Subsidy", "category": "Housing"},
    1: {"name": "Atal Pension Yojana", "desc": "Retirement security with monthly pension.", "benefits": "₹1k-5k Pension", "category": "Pension"},
    2: {"name": "Sukanya Samriddhi", "desc": "Targeted investment for the girl child's future.", "benefits": "8.2% Interest", "category": "Education"},
    3: {"name": "PM-Kisan Nidhi", "desc": "Direct fiscal support for farmers.", "benefits": "₹6,000 / Year", "category": "Agriculture"},
    4: {"name": "Ayushman Bharat", "desc": "Universal healthcare coverage for critical care.", "benefits": "₹5L Health Cover", "category": "Healthcare"}
}

# ==========================================
# I. OPERATIONAL ENGINES
# ==========================================

def get_db():
    conn = sqlite3.connect(CONFIG["DB"])
    conn.row_factory = sqlite3.Row
    return conn

def calculate_priority_score(cat, text):
    """Heuristic Priority Engine with Corruption Override."""
    score = 5
    text = text.lower()
    weights = {"Anti-Corruption": 5, "Police": 4, "Health": 3, "Electricity": 2}
    score += weights.get(cat, 0)
    
    # Emergency Override
    if any(w in text for w in ['urgent', 'emergency', 'danger', 'death', 'bribe']):
        score = 10
    return min(score, 10)

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS complaints 
                     (ticket_id TEXT PRIMARY KEY, name TEXT, email TEXT, district TEXT, 
                      pincode TEXT, problem TEXT, category TEXT, priority TEXT, 
                      status TEXT, timestamp TEXT)''')
init_db()

def dispatch_executive_mail(recipient, name, tid, cat, status):
    """Async-style Mail Dispatch with Error Handling."""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"JanSahay Administration <{CONFIG['MAIL_USER']}>"
        msg['To'] = recipient
        msg['Subject'] = f"Update: {tid} - JanSahay Governance"
        html = render_template('email_template.html', name=name, ticket_id=tid, category=cat, status=status)
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(CONFIG['MAIL_USER'], CONFIG['MAIL_PASS'])
            server.send_message(msg)
    except Exception as e:
        logger.warning(f"Mail Handshake Delay: {e}")

# ==========================================
# II. SYSTEM ROUTES
# ==========================================

@app.route('/')
def home(): return render_template('index.html')

@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    """Neural Ingestion with Department Auto-Assignment."""
    try:
        name, email, text = request.form['name'], request.form['email'], request.form['complaint_text']
        
        # MODEL 1: NLP Prediction
        category = grievance_engine.predict([text])[0] if grievance_engine else "General"
        
        # HYBRID LOGIC: Fixed Corruption misclassification
        if any(w in text.lower() for w in ['bribe', 'corruption', 'money', 'ghoos']):
            category = "Anti-Corruption"
            
        p_score = f"{calculate_priority_score(category, text)}/10"
        tid = f"TKT-{random.randint(10000, 99999)}"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db() as conn:
            conn.execute("INSERT INTO complaints VALUES (?,?,?,?,?,?,?,?,?,?)", 
                         (tid, name, email, request.form['district'], request.form['pincode'], text, category, p_score, "Pending", ts))
        
        dispatch_executive_mail(email, name, tid, category, "Pending")
        return jsonify({'ticket_id': tid, 'category': category, 'priority': p_score})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/track_status', methods=['POST'])
def track_status():
    """Real-time Lifecycle Retrieval."""
    tid = request.form.get('ticket_id', '').strip()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM complaints WHERE ticket_id=?", (tid,)).fetchone()
    if row:
        return jsonify({'success': True, 'name': row['name'], 'category': row['category'], 'status': row['status'], 'priority': row['priority']})
    return jsonify({'success': False, 'message': 'ID Not Found'})

@app.route('/schemes', methods=['GET', 'POST'])
def schemes():
    """Predictive Welfare Engine."""
    recommendations = []
    if request.method == 'POST':
        try:
            age, income = int(request.form.get('age', 0)), int(request.form.get('income', 0))
            gender = 1 if request.form.get('gender') == 'Female' else 0
            if welfare_engine:
                features = np.array([[age, income, gender]])
                pred = int(welfare_engine.predict(features)[0])
                probs = welfare_engine.predict_proba(features)[0]
                if pred in SCHEME_MAP:
                    match = SCHEME_MAP[pred].copy()
                    match['confidence'] = round(np.max(probs) * 100, 1)
                    recommendations.append(match)
        except: pass
    return render_template('schemes.html', recommendations=recommendations)

@app.route('/admin')
def admin_panel():
    if not session.get('admin'): return redirect(url_for('login'))
    with get_db() as conn:
        # SELECT * ensures the 'category' column (Assigned Department) is included
        complaints = conn.execute("SELECT * FROM complaints ORDER BY timestamp DESC").fetchall()
        
        # Necessary for the charts
        cat_stats = conn.execute("SELECT category, COUNT(*) as count FROM complaints GROUP BY category").fetchall()
        stat_stats = conn.execute("SELECT status, COUNT(*) as count FROM complaints GROUP BY status").fetchall()
    
    return render_template('admin.html', 
                           complaints=complaints, 
                           cat_labels=[r['category'] for r in cat_stats], 
                           cat_values=[r['count'] for r in cat_stats],
                           stat_labels=[r['status'] for r in stat_stats], 
                           stat_values=[r['count'] for r in stat_stats])

@app.route('/download_report')
def download_report():
    with get_db() as conn:
        data = conn.execute("SELECT * FROM complaints").fetchall()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "JANSAHAY EXECUTIVE ANALYTICS REPORT", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_fill_color(5, 28, 44); pdf.set_text_color(255, 255, 255)
    pdf.cell(30, 10, "ID", 1, 0, 'C', 1); pdf.cell(50, 10, "Dept", 1, 0, 'C', 1)
    pdf.cell(30, 10, "Score", 1, 0, 'C', 1); pdf.cell(40, 10, "Status", 1, 0, 'C', 1); pdf.cell(40, 10, "Date", 1, 1, 'C', 1)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", '', 10)
    for r in data:
        pdf.cell(30, 10, str(r['ticket_id']), 1); pdf.cell(50, 10, str(r['category']), 1)
        pdf.cell(30, 10, str(r['priority']), 1); pdf.cell(40, 10, str(r['status']), 1); pdf.cell(40, 10, str(r['timestamp'][:10]), 1, 1)
    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=JanSahay_Report.pdf'
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin_panel'))
    return render_template('login.html')

@app.route('/update_status', methods=['POST'])
def update_status():
    tid, new_status = request.form['ticket_id'], request.form['new_status']
    with get_db() as conn:
        row = conn.execute("SELECT name, email, category FROM complaints WHERE ticket_id=?", (tid,)).fetchone()
        if row:
            conn.execute("UPDATE complaints SET status=? WHERE ticket_id=?", (new_status, tid))
            dispatch_executive_mail(row['email'], row['name'], tid, row['category'], new_status)
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)