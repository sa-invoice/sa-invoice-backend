from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from application import db


class Client(db.Model):
    __tablename__ = 'clients'
    client_id = Column(String, primary_key=True)
    client_name = Column(String, nullable=False)
    client_address = Column(String, nullable=False)
    client_city = Column(String, nullable=False)
    client_tin = Column(String, nullable=False, unique=True)
    is_client_taxable = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow)
    invoices = relationship('Invoice', backref='client')
