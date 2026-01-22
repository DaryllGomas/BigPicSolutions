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

def migrate_db():
    """Run database migrations for schema updates"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if address column exists in clients table
    cursor.execute("PRAGMA table_info(clients)")
    client_columns = [col[1] for col in cursor.fetchall()]

    if 'address' not in client_columns:
        cursor.execute('ALTER TABLE clients ADD COLUMN address TEXT DEFAULT ""')
        conn.commit()

    # Check for invoice tracking columns in jobs table
    cursor.execute("PRAGMA table_info(jobs)")
    job_columns = [col[1] for col in cursor.fetchall()]

    if 'invoice_number' not in job_columns:
        cursor.execute('ALTER TABLE jobs ADD COLUMN invoice_number INTEGER')
        conn.commit()

    if 'invoice_status' not in job_columns:
        cursor.execute('ALTER TABLE jobs ADD COLUMN invoice_status TEXT DEFAULT "draft"')
        conn.commit()

    if 'invoice_sent_date' not in job_columns:
        cursor.execute('ALTER TABLE jobs ADD COLUMN invoice_sent_date DATE')
        conn.commit()

    if 'invoice_paid_date' not in job_columns:
        cursor.execute('ALTER TABLE jobs ADD COLUMN invoice_paid_date DATE')
        conn.commit()

    conn.close()


def get_next_invoice_number():
    """Get the next sequential invoice number"""
    conn = get_db_connection()
    cursor = conn.cursor()
    result = cursor.execute('SELECT MAX(invoice_number) FROM jobs').fetchone()[0]
    conn.close()
    return (result or 0) + 1

# Initialize database on startup
init_db()
migrate_db()

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
            INSERT INTO clients (name, email, phone, address, hourly_rate, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('address', ''),
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
            SET name = ?, email = ?, phone = ?, address = ?, hourly_rate = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('name'),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('address', ''),
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

        # Get the next invoice number
        invoice_number = get_next_invoice_number()

        cursor.execute('''
            INSERT INTO jobs (client_id, job_date, description, hours, hourly_rate, total, notes, status, invoice_number, invoice_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(data.get('client_id')),
            data.get('job_date'),
            data.get('description'),
            hours,
            hourly_rate,
            total,
            data.get('notes', ''),
            'draft',
            invoice_number,
            'draft'
        ))
        conn.commit()
        job_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': job_id, 'invoice_number': invoice_number}), 201
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
        SELECT j.*, c.name as client_name, c.email as client_email, c.phone as client_phone, c.address as client_address
        FROM jobs j
        JOIN clients c ON j.client_id = c.id
        WHERE j.id = ?
    ''', (job_id,)).fetchone()

    # Get company settings
    settings = cursor.execute('SELECT * FROM company_settings WHERE id = 1').fetchone()
    conn.close()

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Get invoice number (assign one if missing)
    invoice_number = job['invoice_number']
    if not invoice_number:
        invoice_number = get_next_invoice_number()
        # Update the job with the invoice number
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE jobs SET invoice_number = ? WHERE id = ?', (invoice_number, job_id))
        conn.commit()
        conn.close()

    invoice_id = f"INV-{invoice_number:04d}"

    # Create PDF in memory
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)

    story = []
    styles = getSampleStyleSheet()

    # Brand colors matching the website theme
    brand_deep = colors.HexColor('#0a0f1a')
    brand_horizon = colors.HexColor('#2d4a6f')
    brand_sunrise = colors.HexColor('#f4a261')
    brand_coral = colors.HexColor('#ef8354')
    brand_mist = colors.HexColor('#52616b')

    # Custom styles
    company_name_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=brand_horizon,
        spaceAfter=8,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )

    company_info_style = ParagraphStyle(
        'CompanyInfo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=brand_mist,
        spaceAfter=2,
        alignment=TA_LEFT
    )

    invoice_title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=36,
        textColor=brand_sunrise,
        spaceBefore=20,
        spaceAfter=0,
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold'
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontSize=11,
        textColor=brand_horizon,
        spaceAfter=8,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=brand_deep,
        spaceAfter=4
    )

    # Header section with company info and INVOICE title
    header_data = [
        [Paragraph(settings['company_name'] if settings else "Big Pic Solutions", company_name_style),
         Paragraph("INVOICE", invoice_title_style)]
    ]
    header_table = Table(header_data, colWidths=[4*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)

    # Add spacing after header
    story.append(Spacer(1, 0.15*inch))

    # Company details row
    company_details = []
    if settings:
        company_details.append(Paragraph(settings['owner_name'], company_info_style))
        company_details.append(Paragraph(settings['address'], company_info_style))
        company_details.append(Paragraph(f"{settings['phone']}  •  {settings['email']}", company_info_style))

    for detail in company_details:
        story.append(detail)

    story.append(Spacer(1, 0.4*inch))

    # Invoice details box
    invoice_date = datetime.now().strftime('%B %d, %Y')
    job_date = datetime.fromisoformat(job['job_date']).strftime('%B %d, %Y')

    invoice_details = [
        ['Invoice Number:', invoice_id],
        ['Invoice Date:', invoice_date],
        ['Service Date:', job_date],
        ['Status:', job['invoice_status'].upper() if job['invoice_status'] else 'DRAFT'],
    ]

    details_table = Table(invoice_details, colWidths=[1.5*inch, 2*inch])
    details_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), brand_horizon),
        ('TEXTCOLOR', (1, 0), (1, -1), brand_deep),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (0, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 0.4*inch))

    # Bill To section
    story.append(Paragraph("BILL TO", section_header_style))

    bill_to_lines = [job['client_name']]
    if job['client_address']:
        bill_to_lines.append(job['client_address'])
    if job['client_email']:
        bill_to_lines.append(job['client_email'])
    if job['client_phone']:
        bill_to_lines.append(job['client_phone'])

    for line in bill_to_lines:
        story.append(Paragraph(line, normal_style))

    story.append(Spacer(1, 0.3*inch))

    # Services section
    story.append(Paragraph("SERVICES", section_header_style))

    # Line items table with cleaner design
    line_items = [
        ['Description', 'Hours', 'Rate', 'Amount'],
        [job['description'], f"{job['hours']:.2f}", f"${job['hourly_rate']:.2f}/hr", f"${job['total']:.2f}"],
    ]

    # Add notes as a sub-row if present
    if job['notes']:
        line_items.append([Paragraph(f"<i>Note: {job['notes']}</i>", ParagraphStyle('Note', fontSize=9, textColor=brand_mist)), '', '', ''])

    line_table = Table(line_items, colWidths=[3.5*inch, 1*inch, 1.25*inch, 1.25*inch])
    line_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 0), (-1, 0), brand_horizon),
        ('TEXTCOLOR', (0, 1), (-1, -1), brand_deep),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#e9ecef')),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 0.2*inch))

    # Totals section - right aligned
    totals_data = [
        ['Subtotal:', f"${job['total']:.2f}"],
        ['Tax (0%):', '$0.00'],
        ['TOTAL DUE:', f"${job['total']:.2f}"],
    ]

    totals_table = Table(totals_data, colWidths=[1.5*inch, 1.25*inch])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -2), brand_mist),
        ('TEXTCOLOR', (0, -1), (-1, -1), brand_sunrise),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, -1), (-1, -1), 2, brand_sunrise),
    ]))

    # Right align the totals table
    totals_wrapper = Table([[totals_table]], colWidths=[7*inch])
    totals_wrapper.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
    ]))
    story.append(totals_wrapper)

    story.append(Spacer(1, 0.6*inch))

    # Footer
    company_name = settings['company_name'] if settings else "Big Pic Solutions"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=brand_horizon,
        alignment=TA_CENTER,
        spaceBefore=20
    )
    story.append(Paragraph("Thank you for your business!", footer_style))

    subfooter_style = ParagraphStyle(
        'SubFooter',
        parent=styles['Normal'],
        fontSize=9,
        textColor=brand_mist,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"{company_name} • AI-Powered Technology Consulting", subfooter_style))

    # Build PDF with optional PAID watermark
    if job['invoice_status'] == 'paid':
        from reportlab.pdfgen import canvas as pdf_canvas

        def add_paid_watermark(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica-Bold', 72)
            canvas.setFillColor(colors.Color(0.2, 0.8, 0.4, alpha=0.25))  # Light green
            canvas.translate(4.25*inch, 5.5*inch)
            canvas.rotate(45)
            canvas.drawCentredString(0, 0, "PAID")
            canvas.restoreState()

        doc.build(story, onFirstPage=add_paid_watermark, onLaterPages=add_paid_watermark)
    else:
        doc.build(story)

    # Return PDF
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'Invoice-{invoice_id}.pdf')

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


@app.route('/api/jobs/<int:job_id>/status', methods=['PUT'])
def update_invoice_status(job_id):
    """Update invoice status (draft, sent, paid)"""
    data = request.json
    new_status = data.get('invoice_status')

    if new_status not in ['draft', 'sent', 'paid']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get current job data
        job = cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
        if not job:
            conn.close()
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        # Assign invoice number if not already assigned
        invoice_number = job['invoice_number']
        if not invoice_number:
            invoice_number = get_next_invoice_number()
            cursor.execute('UPDATE jobs SET invoice_number = ? WHERE id = ?', (invoice_number, job_id))

        # Update status and relevant dates
        today = datetime.now().strftime('%Y-%m-%d')

        if new_status == 'sent':
            cursor.execute('''
                UPDATE jobs SET invoice_status = ?, invoice_sent_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_status, today, job_id))
        elif new_status == 'paid':
            cursor.execute('''
                UPDATE jobs SET invoice_status = ?, invoice_paid_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_status, today, job_id))
        else:  # draft - clear dates
            cursor.execute('''
                UPDATE jobs SET invoice_status = ?, invoice_sent_date = NULL, invoice_paid_date = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_status, job_id))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'invoice_number': invoice_number, 'status': new_status})
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
