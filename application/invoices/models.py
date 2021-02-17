from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Integer
from sqlalchemy.orm import relationship
from application import db


class Invoice(db.Model):
    __tablename__ = 'invoices'

    invoice_id = Column(String, unique=True)
    invoice_number = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String, ForeignKey('clients.client_id'))
    invoice_items = relationship('InvoiceItem', backref='invoice')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    invoice_gross_amount = Column(Float, nullable=False)
    total_discount_amount = Column(Float, nullable=False)
    total_tax_amount = Column(Float, nullable=False)
    invoice_net_amount = Column(Float, nullable=False)

    # Copy these fields from Client details as they ar subject to change
    client_name = Column(String, nullable=False)
    client_tin = Column(String, nullable=False)
    client_address = Column(String, nullable=False)
    client_city = Column(String, nullable=False)
    is_client_taxable = Column(String, nullable=False)


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'

    invoice_item_id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey('products.product_id'))
    invoice_id = Column(String, ForeignKey('invoices.invoice_id'))
    product_quantity = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    markup_amount = Column(Float, nullable=False)
    gross_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False)
    amount_after_discount = Column(Float, nullable=False)
    vat_amount = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)

    # Copy these fields from Product details as they ar subject to change
    product_name = Column(String, nullable=False)
    product_price = Column(Float, nullable=False)
    product_price_currency = Column(String, nullable=False)
    product_discount_percent = Column(Float, nullable=False)
    product_markup_percent = Column(Float, nullable=False)
    product_vat_percent = Column(Float, nullable=False)