import os
from datetime import datetime
from uuid import uuid4

import jinja2
from flask import Blueprint, jsonify, request, send_file
import pdfkit

from application import db
from application.clients.routes import get_client_by_id
from application.invoices.models import Invoice, InvoiceItem
from application.invoices.schemas import invoices_schema, invoice_schema
from application.products.routes import get_product_by_id
from definitions import ROOT_DIR

invoices_api = Blueprint('invoices_api', __name__)
template_dir = os.path.join(ROOT_DIR, 'templates')
pdf_dir = os.path.join(ROOT_DIR, 'pdf')
template_loader = jinja2.FileSystemLoader(searchpath=template_dir)
template_env = jinja2.Environment(loader=template_loader)
pdfkit_config = pdfkit.configuration(wkhtmltopdf='/app/bin/wkhtmltopdf') if 'DYNO' in os.environ else None


@invoices_api.route('', methods=['POST'])
def create_invoice(**kwargs):
    is_dryrun = request.args.get('dryrun').lower() in ('true', '1')
    try:
        data = request.get_json()
        invoice_id = uuid4().hex
        data['invoice_id'] = invoice_id
        data['invoice_gross_amount'] = 0
        data['invoice_number'] = None
        data['invoice_gross_amount'] = 0
        data['total_discount_amount'] = 0
        data['total_tax_amount'] = 0
        data['invoice_net_amount'] = 0
        client_details = get_client_by_id(data['client_id'])
        is_client_taxable = getattr(client_details, 'is_client_taxable')
        if not client_details:
            return jsonify(status='ERROR', error_code='CLIENT_NOT_FOUND', message='Client not found!'), 404

        # Make copy of client details as they are subject to changes
        data['client_name'] = getattr(client_details, 'client_name')
        data['client_address'] = getattr(client_details, 'client_address')
        data['client_city'] = getattr(client_details, 'client_city')
        data['client_tin'] = getattr(client_details, 'client_tin')
        data['is_client_taxable'] = is_client_taxable

        invoice_items = data['invoice_items']
        if len(invoice_items) < 1:
            return jsonify(status='ERROR', errors=['Invoice must contain at least one invoice item']), 400
        for i in range(len(invoice_items)):
            product = get_product_by_id(invoice_items[i]['product_id'])
            if not product:
                return jsonify(error_code='PRODUCT_NOT_FOUND', message='Product with id ' + invoice_items[i]['product_id'] +  ' not found!'), 404
            price_per_unit = getattr(product, 'product_price')
            vat_percent = getattr(product, 'product_vat_percent')
            discount_percent = invoice_items[i]['product_discount_percent']
            markup_percent = invoice_items[i]['product_markup_percent']
            quantity = invoice_items[i]['product_quantity']
            total_price = price_per_unit * quantity
            markup_amount = total_price * (markup_percent / 100)
            gross_amount = total_price + markup_amount
            discount_amount = gross_amount * (discount_percent / 100)
            amount_after_discount = gross_amount - discount_amount
            vat_amount = amount_after_discount * (vat_percent / 100) if is_client_taxable else 0
            net_amount = amount_after_discount + vat_amount

            # Make copy of these entries as product details are subject to change
            invoice_items[i]['product_price'] = price_per_unit
            invoice_items[i]['product_price_currency'] = getattr(product, 'product_price_currency')
            invoice_items[i]['product_name'] = getattr(product, 'product_name')
            invoice_items[i]['product_vat_percent'] = vat_percent

            # Save calculations to the database
            invoice_items[i]['total_price'] = total_price
            invoice_items[i]['markup_amount'] = markup_amount
            invoice_items[i]['gross_amount'] = gross_amount
            data['invoice_gross_amount'] += gross_amount
            invoice_items[i]['discount_amount'] = discount_amount
            data['total_discount_amount'] += discount_amount
            invoice_items[i]['amount_after_discount'] = amount_after_discount
            invoice_items[i]['vat_amount'] = vat_amount
            data['total_tax_amount'] += vat_amount
            invoice_items[i]['net_amount'] = net_amount
            data['invoice_net_amount'] += net_amount

            item = InvoiceItem(**invoice_items[i], invoice_item_id=uuid4().hex)
            data['invoice_items'][i] = item
        invoice = Invoice(**data)
        if not is_dryrun:
            db.session.add(invoice)
            db.session.commit()
        return jsonify(status='SUCCESS', message='Invoice created successfully!', invoice_details=invoice_schema.dump(invoice)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(status='ERROR', errors=e.args), 400


@invoices_api.route('', methods=['GET'])
def get_invoices():
    try:
        query_result = Invoice.query.all()
        invoices = invoices_schema.dump(query_result)
        return jsonify(invoices), 200
    except Exception as e:
        return jsonify(status='ERROR', errors=e.args), 400


@invoices_api.route('<invoice_id>', methods=['GET'])
def get_invoice(invoice_id: str):
    try:
        query_result = Invoice.query.filter_by(invoice_id=invoice_id).first()
        invoice = invoice_schema.dump(query_result)
        return jsonify(invoice), 200
    except Exception as e:
        return jsonify(status='ERROR', errors=e.args), 400


@invoices_api.route('<invoice_id>/download', methods=['GET'])
def download_invoice(invoice_id: str):
    try:
        query_result = Invoice.query.filter_by(invoice_id=invoice_id).first()
        invoice = invoice_schema.dump(query_result)
        invoice['invoice_number'] = str(invoice['invoice_number']).zfill(8)
        invoice['created_at'] = datetime.fromisoformat(invoice['created_at'])
        template = template_env.get_template('invoice_template.html')
        html = template.render(invoice=invoice, currency='SAR')
        filename = f'invoice_{invoice["invoice_number"]}.pdf'
        filepath = f'{pdf_dir}/{filename}'
        pdfkit.from_string(html, filepath, configuration=pdfkit_config)
        return send_file(filepath, attachment_filename=filename), 200
    except Exception as e:
        return jsonify(status='ERROR', errors=e.args), 400