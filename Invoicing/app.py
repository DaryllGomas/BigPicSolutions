#!/usr/bin/env python3
"""
Big Pic Solutions Invoicing System
Professional invoicing and client tracking for IT consulting
"""

from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import sqlite3
import os
import json
import csv
from io import BytesIO, StringIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

app = Flask(__name__, static_folder='static', template_folder='templates')

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with schema"""
    if os.path.exists(DB_PATH):
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Create clients table
    cursor.execute('''
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            hourly_rate REAL NOT NULL DEFAULT 140.00,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create jobs table
    cursor.execute('''
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            job_date DATE NOT NULL,
            description TEXT NOT NULL,
            hours REAL NOT NULL,
            hourly_rate REAL NOT NULL,
            total REAL NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    ''')

    # Create company settings table
    cursor.execute('''
        CREATE TABLE company_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            company_name TEXT NOT NULL DEFAULT 'Big Pic Solutions',
            owner_name TEXT NOT NULL DEFAULT 'Daryll Gomas',
            address TEXT NOT NULL DEFAULT '4116 SE 79th Ave, Portland, Oregon 97206',
            phone TEXT NOT NULL DEFAULT '727-475-4153',
            email TEXT NOT NULL DEFAULT 'daryll.gomas@gmail.com',
            default_hourly_rate REAL NOT NULL DEFAULT 140.00,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert default company settings
    cursor.execute('''
        INSERT INTO company_settings (id, company_name, owner_name, address, phone, email, default_hourly_rate)
        VALUES (1, 'Big Pic Solutions', 'Daryll Gomas', '4116 SE 79th Ave, Portland, Oregon 97206', '727-475-4153', 'daryll.gomas@gmail.com', 140.00)
    ''')

    # Create goals table
    cursor.execute('''
        CREATE TABLE goals (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            yearly_net_goal REAL NOT NULL DEFAULT 30000.00,
            yearly_gross_goal REAL NOT NULL DEFAULT 43500.00,
            tax_rate REAL NOT NULL DEFAULT 0.31,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert default goals (based on $30k net, ~31% tax rate)
    cursor.execute('''
        INSERT INTO goals (id, yearly_net_goal, yearly_gross_goal, tax_rate)
        VALUES (1, 30000.00, 43500.00, 0.31)
    ''')

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# ============== CLIENT ROUTES ==============

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/clients', methods=['GET'])
def get_clients():
    """Get all clients"""
    conn = get_db_connection()
    cursor = conn.cursor()
    clients = cursor.execute('SELECT * FROM clients ORDER BY name').fetchall()
    conn.close()
    return jsonify([dict(c) for c in clients])

@app.route('/api/clients', methods=['POST'])
def add_client():
    """Add a new client"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO clients (name, email, phone, hourly_rate, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('email', ''),
            data.get('phone', ''),
            float(data.get('hourly_rate', 140.00)),
            data.get('notes', '')
        ))
        conn.commit()
        client_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': client_id}), 201
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    """Get a specific client"""
    conn = get_db_connection()
    cursor = conn.cursor()
    client = cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()
    conn.close()

    if not client:
        return jsonify({'error': 'Client not found'}), 404
    return jsonify(dict(client))

@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    """Update a client"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE clients
            SET name = ?, email = ?, phone = ?, hourly_rate = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('name'),
            data.get('email', ''),
            data.get('phone', ''),
            float(data.get('hourly_rate', 140.00)),
            data.get('notes', ''),
            client_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

# ============== JOB/INVOICE ROUTES ==============

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs, optionally filtered by client"""
    client_id = request.args.get('client_id')
    conn = get_db_connection()
    cursor = conn.cursor()

    if client_id:
        jobs = cursor.execute('''
            SELECT j.*, c.name as client_name
            FROM jobs j
            JOIN clients c ON j.client_id = c.id
            WHERE j.client_id = ?
            ORDER BY j.job_date DESC
        ''', (client_id,)).fetchall()
    else:
        jobs = cursor.execute('''
            SELECT j.*, c.name as client_name
            FROM jobs j
            JOIN clients c ON j.client_id = c.id
            ORDER BY j.job_date DESC
        ''').fetchall()

    conn.close()
    return jsonify([dict(j) for j in jobs])

@app.route('/api/jobs', methods=['POST'])
def add_job():
    """Add a new job"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        hours = float(data.get('hours', 0))
        hourly_rate = float(data.get('hourly_rate', 140.00))
        total = hours * hourly_rate

        cursor.execute('''
            INSERT INTO jobs (client_id, job_date, description, hours, hourly_rate, total, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(data.get('client_id')),
            data.get('job_date'),
            data.get('description'),
            hours,
            hourly_rate,
            total,
            data.get('notes', ''),
            'draft'
        ))
        conn.commit()
        job_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': job_id}), 201
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get a specific job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    job = cursor.execute('''
        SELECT j.*, c.name as client_name, c.email as client_email, c.phone as client_phone
        FROM jobs j
        JOIN clients c ON j.client_id = c.id
        WHERE j.id = ?
    ''', (job_id,)).fetchone()
    conn.close()

    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(dict(job))

@app.route('/api/jobs/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    """Update a job"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        hours = float(data.get('hours', 0))
        hourly_rate = float(data.get('hourly_rate', 140.00))
        total = hours * hourly_rate

        cursor.execute('''
            UPDATE jobs
            SET job_date = ?, description = ?, hours = ?, hourly_rate = ?, total = ?, notes = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('job_date'),
            data.get('description'),
            hours,
            hourly_rate,
            total,
            data.get('notes', ''),
            data.get('status', 'draft'),
            job_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/jobs/<int:job_id>/pdf', methods=['GET'])
def generate_pdf(job_id):
    """Generate PDF invoice for a job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    job = cursor.execute('''
        SELECT j.*, c.name as client_name, c.email as client_email, c.phone as client_phone
        FROM jobs j
        JOIN clients c ON j.client_id = c.id
        WHERE j.id = ?
    ''', (job_id,)).fetchone()

    # Get company settings
    settings = cursor.execute('SELECT * FROM company_settings WHERE id = 1').fetchone()
    conn.close()

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Create PDF in memory
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=6,
        alignment=TA_LEFT
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=12,
        spaceBefore=12
    )

    company_info_style = ParagraphStyle(
        'CompanyInfo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=4,
        alignment=TA_LEFT
    )

    # Company header (top left)
    story.append(Paragraph(settings['company_name'] if settings else "Big Pic Solutions", title_style))
    if settings:
        story.append(Paragraph(settings['owner_name'], company_info_style))
        story.append(Paragraph(settings['address'], company_info_style))
        story.append(Paragraph(settings['phone'], company_info_style))
        story.append(Paragraph(settings['email'], company_info_style))
    story.append(Spacer(1, 0.3*inch))

    # Invoice title
    story.append(Paragraph("INVOICE", heading_style))
    story.append(Spacer(1, 0.2*inch))

    # Invoice details
    details_data = [
        ['Invoice #:', f"JOB-{job_id:05d}", 'Date:', datetime.now().strftime('%Y-%m-%d')],
        ['Client:', job['client_name'], 'Due Date:', (datetime.fromisoformat(job['job_date'])).strftime('%Y-%m-%d')],
    ]

    details_table = Table(details_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
    details_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0066cc')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(details_table)
    story.append(Spacer(1, 0.3*inch))

    # Bill to section
    story.append(Paragraph("Bill To:", heading_style))
    bill_to = f"{job['client_name']}"
    if job['client_email']:
        bill_to += f"<br/>{job['client_email']}"
    if job['client_phone']:
        bill_to += f"<br/>{job['client_phone']}"
    story.append(Paragraph(bill_to, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    # Service description
    story.append(Paragraph("Service Description:", heading_style))
    story.append(Paragraph(job['description'], styles['Normal']))
    if job['notes']:
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("<b>Notes:</b>", styles['Normal']))
        story.append(Paragraph(job['notes'], styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    # Line items table
    line_items = [
        ['Description', 'Hours', 'Rate', 'Total'],
        [job['description'][:40], f"{job['hours']}", f"${job['hourly_rate']:.2f}", f"${job['total']:.2f}"],
        ['', '', '', ''],
        ['', '', 'Subtotal:', f"${job['total']:.2f}"],
        ['', '', 'Tax (0%):', '$0.00'],
        ['', '', 'TOTAL:', f"${job['total']:.2f}"],
    ]

    line_table = Table(line_items, colWidths=[3*inch, 1*inch, 1.2*inch, 1.3*inch])
    line_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#0066cc')),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#0066cc')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#0066cc')),
        ('GRID', (0, -4), (-1, -2), 0.5, colors.grey),
    ]))

    story.append(line_table)
    story.append(Spacer(1, 0.4*inch))

    # Footer
    company_name = settings['company_name'] if settings else "Big Pic Solutions"
    footer_text = f"Thank you for your business! {company_name} - AI-Powered Technology Consulting"
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )))

    # Build PDF
    doc.build(story)

    # Return PDF
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'Invoice-JOB-{job_id:05d}.pdf')

@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

# ============== STATS ROUTE ==============

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    total_revenue = cursor.execute('SELECT SUM(total) FROM jobs').fetchone()[0] or 0
    total_hours = cursor.execute('SELECT SUM(hours) FROM jobs').fetchone()[0] or 0
    total_clients = cursor.execute('SELECT COUNT(*) FROM clients').fetchone()[0]
    total_jobs = cursor.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]

    # Get current year revenue
    current_year = datetime.now().year
    year_revenue = cursor.execute(
        "SELECT SUM(total) FROM jobs WHERE strftime('%Y', job_date) = ?",
        (str(current_year),)
    ).fetchone()[0] or 0

    # Get current month revenue
    current_month = datetime.now().strftime('%Y-%m')
    month_revenue = cursor.execute(
        "SELECT SUM(total) FROM jobs WHERE strftime('%Y-%m', job_date) = ?",
        (current_month,)
    ).fetchone()[0] or 0

    # Get current week revenue (last 7 days)
    week_revenue = cursor.execute(
        "SELECT SUM(total) FROM jobs WHERE job_date >= date('now', '-7 days')",
    ).fetchone()[0] or 0

    conn.close()

    return jsonify({
        'total_revenue': round(total_revenue, 2),
        'total_hours': round(total_hours, 2),
        'total_clients': total_clients,
        'total_jobs': total_jobs,
        'year_revenue': round(year_revenue, 2),
        'month_revenue': round(month_revenue, 2),
        'week_revenue': round(week_revenue, 2)
    })

# ============== COMPANY SETTINGS ROUTES ==============

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get company settings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    settings = cursor.execute('SELECT * FROM company_settings WHERE id = 1').fetchone()
    conn.close()

    if not settings:
        return jsonify({'error': 'Settings not found'}), 404
    return jsonify(dict(settings))

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update company settings"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE company_settings
            SET company_name = ?, owner_name = ?, address = ?, phone = ?, email = ?, default_hourly_rate = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        ''', (
            data.get('company_name', 'Big Pic Solutions'),
            data.get('owner_name', 'Daryll Gomas'),
            data.get('address', ''),
            data.get('phone', ''),
            data.get('email', ''),
            float(data.get('default_hourly_rate', 140.00))
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

# ============== GOALS ROUTES ==============

@app.route('/api/goals', methods=['GET'])
def get_goals():
    """Get financial goals with breakdowns"""
    conn = get_db_connection()
    cursor = conn.cursor()
    goals = cursor.execute('SELECT * FROM goals WHERE id = 1').fetchone()
    conn.close()

    if not goals:
        # Return default values if not found
        goals = {
            'yearly_net_goal': 30000.00,
            'yearly_gross_goal': 43500.00,
            'tax_rate': 0.31
        }
    else:
        goals = dict(goals)

    # Calculate breakdowns
    yearly_gross = goals['yearly_gross_goal']
    yearly_net = goals['yearly_net_goal']

    return jsonify({
        'yearly_gross': round(yearly_gross, 2),
        'yearly_net': round(yearly_net, 2),
        'monthly_gross': round(yearly_gross / 12, 2),
        'monthly_net': round(yearly_net / 12, 2),
        'weekly_gross': round(yearly_gross / 52, 2),
        'weekly_net': round(yearly_net / 52, 2),
        'daily_gross': round(yearly_gross / 365, 2),
        'daily_net': round(yearly_net / 365, 2),
        'tax_rate': goals['tax_rate']
    })

# ============== EXPORT ROUTES ==============

@app.route('/api/export/clients', methods=['GET'])
def export_clients():
    """Export all clients to CSV"""
    conn = get_db_connection()
    cursor = conn.cursor()
    clients = cursor.execute('SELECT * FROM clients ORDER BY name').fetchall()
    conn.close()

    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Hourly Rate', 'Notes', 'Created At', 'Updated At'])

    # Write data
    for client in clients:
        writer.writerow([
            client['id'],
            client['name'],
            client['email'],
            client['phone'],
            client['hourly_rate'],
            client['notes'],
            client['created_at'],
            client['updated_at']
        ])

    # Prepare response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'clients_export_{timestamp}.csv'
    )

@app.route('/api/export/jobs', methods=['GET'])
def export_jobs():
    """Export all jobs to CSV"""
    conn = get_db_connection()
    cursor = conn.cursor()
    jobs = cursor.execute('''
        SELECT j.*, c.name as client_name
        FROM jobs j
        LEFT JOIN clients c ON j.client_id = c.id
        ORDER BY j.job_date DESC
    ''').fetchall()
    conn.close()

    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['ID', 'Client Name', 'Job Date', 'Description', 'Hours', 'Hourly Rate', 'Total', 'Notes', 'Status', 'Created At'])

    # Write data
    for job in jobs:
        writer.writerow([
            job['id'],
            job['client_name'],
            job['job_date'],
            job['description'],
            job['hours'],
            job['hourly_rate'],
            job['total'],
            job['notes'],
            job['status'],
            job['created_at']
        ])

    # Prepare response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'jobs_export_{timestamp}.csv'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
