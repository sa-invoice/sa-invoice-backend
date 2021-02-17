from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import relationship
from application import db


class Product(db.Model):
    __tablename__ = 'products'
    product_id = Column(String, primary_key=True, nullable=False)
    product_name = Column(String, nullable=False)
    product_description = Column(String, nullable=True)
    product_price_currency = Column(String, nullable=False, default='SAR')
    product_price = Column(Float, nullable=False)
    product_discount_percent = Column(Float, nullable=False, default=0)
    product_markup_percent = Column(Float, nullable=False, default=20)
    product_vat_percent = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow)
    invoice_items = relationship('InvoiceItem', backref='product')
