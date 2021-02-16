from datetime import datetime

from uuid import uuid4

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, event, engine, Integer
import os
from flask_marshmallow import Marshmallow
from sqlalchemy.engine import Engine
from sqlalchemy.orm import relationship

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'invoice_system.db')

db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database Created!')


@app.cli.command('db_drop')
def drop_all():
    db.drop_all()
    print('Database dropped!')


@app.cli.command('db_seed')
def db_seed():
    insert_product(
        product_name='Printing',
        product_description='Print various sizes',
        product_price=50,
        product_vat_percent=5
    )
    insert_client(
        client_name='Alpha Tech',
        client_tin='82375628377',
        client_address='Somewhere on the earth',
        client_city='Jedda',
        is_client_taxable=True
    )
    print('Database seeded!')


def insert_product(**args):
    args['product_id'] = uuid4().hex
    args['created_at'] = None
    args['last_updated_at'] = None
    product = Product(**args)
    db.session.add(product)
    db.session.commit()
    return product


def insert_client(**args):
    args['client_id'] = uuid4().hex
    args['created_at'] = None
    args['last_updated_at'] = None
    client = Client(**args)
    db.session.add(client)
    db.session.commit()
    return client


@app.route('/')
def root_route():
    return jsonify(message='There is nothing here'), 404


@app.route('/api/products', methods=['GET'])
def get_products():
    query_result = Product.query.all()
    products_list = products_schema.dump(query_result)
    return jsonify(products_list)


def get_product_by_id(product_id: str):
    return Product.query.filter_by(product_id=product_id).first()


@app.route('/api/products/<product_id>', methods=['PUT'])
def put_product_details(product_id: str):
    try:
        row = get_product_by_id(product_id)
        if row:
            data = request.get_json()
            exclude_columns = ('created_at', 'last_updated_at', 'product_id')
            for column_name in data:
                if column_name not in exclude_columns:
                    setattr(row, column_name, data[column_name])
            setattr(row, 'last_updated_at', datetime.utcnow())
            db.session.commit()
            return jsonify(status='SUCCESS', message='Product updated successfully!', updated_product=product_schema.dump(row)), 200
        else:
            return jsonify(error_code='PRODUCT_NOT_FOUND', message='Product not found!'), 404
    except Exception as e:
        db.session.rollback()
        return jsonify(status='ERROR', errors=e.args), 400


@app.route('/api/products/<product_id>', methods=['GET'])
def get_product_details(product_id: str):
    row = get_product_by_id(product_id)
    if row:
        return jsonify(product_schema.dump(row)), 200
    else:
        return jsonify(error_code='PRODUCT_NOT_FOUND', message='Product not found!'), 404


@app.route('/api/products', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        product = insert_product(**data)
        product = product_schema.dump(product)
        return jsonify(status='SUCCESS', message='Product added successfully!', added_product=product), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(status='ERROR', errors=e.args), 400


def get_client_by_id(client_id: str):
    return Client.query.filter_by(client_id=client_id).first()


@app.route('/api/clients', methods=['POST'])
def add_client():
    try:
        data = request.get_json()
        client = insert_client(**data)
        return jsonify(status='SUCCESS', message='Client added successfully!', added_client=client_schema.dump(client)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(status='ERROR', errors=e.args), 400


@app.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        query_result = Client.query.all()
        clients_list = clients_schema.dump(query_result)
        return jsonify(clients_list)
    except Exception as e:
        return jsonify(status='ERROR', errors=e.args), 400


@app.route('/api/clients/<client_id>', methods=['GET'])
def get_client_details(client_id: str):
    try:
        row = get_client_by_id(client_id)
        if row:
            return jsonify(client_schema.dump(row)), 200
        else:
            return jsonify(error_code='CLIENT_NOT_FOUND', message='Client not found!'), 404
    except Exception as e:
        return jsonify(status='ERROR', errors=e.args), 400


@app.route('/api/clients/<client_id>', methods=['PUT'])
def put_client_details(client_id: str):
    try:
        row = get_client_by_id(client_id)
        if row:
            data = request.get_json()
            exclude_columns = ('created_at', 'last_updated_at', 'client_id')
            for column_name in data:
                if column_name not in exclude_columns:
                    setattr(row, column_name, data[column_name])
            setattr(row, 'last_updated_at', datetime.utcnow())
            db.session.commit()
            return jsonify(status='SUCCESS', message='Client updated successfully!', updated_client=client_schema.dump(row)), 200
        else:
            return jsonify(status='ERROR', error_code='CLIENT_NOT_FOUND', message='Client not found!'), 404
    except Exception as e:
        db.session.rollback()
        return jsonify(status='ERROR', errors=e.args), 400


@app.route('/api/invoices', methods=['POST'])
def create_invoice():
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
        if not client_details:
            return jsonify(status='ERROR', error_code='CLIENT_NOT_FOUND', message='Client not found!'), 404
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
            vat_amount = amount_after_discount * (vat_percent / 100)
            net_amount = amount_after_discount + vat_amount
            invoice_items[i]['product_price'] = price_per_unit
            invoice_items[i]['product_price_currency'] = getattr(product, 'product_price_currency')
            invoice_items[i]['product_name'] = getattr(product, 'product_name')
            invoice_items[i]['product_vat_percent'] = vat_percent
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
        db.session.add(invoice)
        db.session.commit()
        return jsonify(status='SUCCESS', message='Invoice created successfully!', invoice_details=invoice_schema.dump(invoice)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(status='ERROR', errors=e.args), 400


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


class ProductSchema(ma.Schema):
    class Meta:
        fields = (
            'product_id',
            'product_name',
            'product_description',
            'product_price_currency',
            'product_price',
            'product_discount_percent',
            'product_vat_percent'
            'product_markup_percent'
        )


product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


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


class ClientSchema(ma.Schema):
    class Meta:
        fields = (
            'client_id',
            'client_name',
            'client_tin',
            'client_address',
            'client_city',
            'is_client_taxable'
        )


client_schema = ClientSchema()
clients_schema = ClientSchema(many=True)


class Invoice(db.Model):
    __tablename__ = 'invoices'
    invoice_id = Column(String, unique=True)
    invoice_number = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String, ForeignKey('clients.client_id'))
    invoice_items = relationship('InvoiceItem', backref='invoice')
    client_details = relationship('Client', backref='invoice')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    invoice_gross_amount = Column(Float, nullable=False)
    total_discount_amount = Column(Float, nullable=False)
    total_tax_amount = Column(Float, nullable=False)
    invoice_net_amount = Column(Float, nullable=False)


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    invoice_item_id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey('products.product_id'))
    invoice_id = Column(String, ForeignKey('invoices.invoice_id'))
    product_name = Column(String, nullable=False)
    product_price = Column(Float, nullable=False)
    product_quantity = Column(Float, nullable=False)
    product_price_currency = Column(String, nullable=False)
    product_discount_percent = Column(Float, nullable=False)
    product_markup_percent = Column(Float, nullable=False)
    product_vat_percent = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    markup_amount = Column(Float, nullable=False)
    gross_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False)
    amount_after_discount = Column(Float, nullable=False)
    vat_amount = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)


class InvoiceItemSchema(ma.Schema):
    class Meta:
        fields = (
            'invoice_item_id',
            'product_id',
            'invoice_id',
            'product_name',
            'product_price',
            'product_quantity',
            'product_price_currency',
            'product_discount_percent',
            'product_markup_percent',
            'product_vat_percent',
            'total_price',
            'markup_amount',
            'gross_amount',
            'discount_amount',
            'amount_after_discount',
            'vat_amount',
            'net_amount'
        )


class InvoiceSchema(ma.Schema):
    invoice_id = fields.String()
    invoice_number = fields.Integer()
    invoice_items = fields.List(fields.Nested(InvoiceItemSchema(exclude=('invoice_id',))))
    client_details = fields.Nested(ClientSchema)
    created_at = fields.DateTime()
    invoice_gross_amount = fields.Float()
    total_discount_amount = fields.Float()
    total_tax_amount = fields.Float()
    invoice_net_amount = fields.Float()


invoice_schema = InvoiceSchema()
invoices_schema = InvoiceSchema(many=True)



if __name__ == '__main__':
    app.run()
