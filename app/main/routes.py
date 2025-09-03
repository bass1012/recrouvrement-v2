from flask import render_template, request, send_file, redirect, url_for, flash
from flask_login import login_required, current_user
from . import main
from ..models import Client, EmailLog
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from sqlalchemy import or_

@main.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Client.query
    
    if search:
        query = query.filter(
            or_(
                Client.nom.contains(search),
                Client.email.contains(search),
                Client.telephone.contains(search)
            )
        )
    
    if status_filter:
        query = query.filter(Client.statut == status_filter)
    
    clients = query.all()
    
    today = datetime.now().date()
    for client in clients:
        if client.date_expiration:
            days_until_expiry = (client.date_expiration - today).days
            if days_until_expiry <= 2:
                client.alert_class = 'table-danger'
            elif days_until_expiry <= 7:
                client.alert_class = 'table-warning'
            else:
                client.alert_class = ''
        else:
            client.alert_class = ''
    
    return render_template('index.html', clients=clients, search=search, status_filter=status_filter, datetime=datetime)

@main.route('/dashboard')
@login_required
def dashboard():
    total_clients = Client.query.count()
    clients_actifs = Client.query.filter_by(statut='actif').count()
    clients_inactifs = Client.query.filter_by(statut='inactif').count()
    
    today = datetime.now().date()
    expiring_soon = Client.query.filter(
        Client.date_expiration <= today + timedelta(days=7),
        Client.statut == 'actif'
    ).count()
    
    six_months_ago = today - timedelta(days=180)
    clients_recent = Client.query.filter(Client.date_ajout >= six_months_ago).all()
    
    monthly_data = {}
    for client in clients_recent:
        month_key = client.date_ajout.strftime('%Y-%m')
        monthly_data[month_key] = monthly_data.get(month_key, 0) + 1
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    emails_sent = EmailLog.query.filter(
        EmailLog.date_envoi >= thirty_days_ago,
        EmailLog.statut == 'envoyé'
    ).count()
    
    return render_template('dashboard.html', 
                         total_clients=total_clients,
                         clients_actifs=clients_actifs,
                         clients_inactifs=clients_inactifs,
                         expiring_soon=expiring_soon,
                         monthly_data=monthly_data,
                         emails_sent=emails_sent)

@main.route('/export/excel')
@login_required
def export_excel():
    clients = Client.query.all()
    
    data = []
    for client in clients:
        data.append({
            'ID': client.id,
            'Nom': client.nom,
            'Email': client.email,
            'Téléphone': client.telephone or '',
            'Date d\'ajout': client.date_ajout.strftime('%d/%m/%Y') if client.date_ajout else '',
            'Date d\'expiration': client.date_expiration.strftime('%d/%m/%Y') if client.date_expiration else '',
            'Dernière visite': client.date_derniere_visite.strftime('%d/%m/%Y') if client.date_derniere_visite else '',
            'Statut': client.statut,
            'Notes': client.notes or ''
        })
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Clients', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'clients_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@main.route('/export/pdf')
@login_required
def export_pdf():
    clients = Client.query.all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    data = [['Nom', 'Email', 'Téléphone', 'Statut', 'Expiration']]
    
    for client in clients:
        data.append([
            client.nom,
            client.email,
            client.telephone or '',
            client.statut,
            client.date_expiration.strftime('%d/%m/%Y') if client.date_expiration else ''
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    doc.build([table])
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'clients_{datetime.now().strftime("%Y%m%d")}.pdf'
    )
