from datetime import datetime

from uuid import uuid4
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
import os
from flask_marshmallow import Marshmallow
from sqlalchemy.exc import NoSuchTableError

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'invoice_system.db')

db = SQLAlchemy(app)
ma = Marshmallow(app)


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
    print('Database seeded!')


def insert_product(**args):
    args['product_id'] = uuid4().hex
    product = Product(**args)
    db.session.add(product)
    db.session.commit()
    return product


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


@app.route('/api/products/<product_id>', methods=['GET'])
def get_product_details(product_id: str):
    row = get_product_by_id(product_id)
    if row:
        return jsonify(product_schema.dump(row)), 200
    else:
        return jsonify(error_code='PRODUCT_NOT_FOUND', message='Product not found!'), 404


@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.get_json()
    product = insert_product(**data)
    product = product_schema.dump(product)
    return jsonify(status='SUCCESS', message='Product added successfully', added_product=product), 201


@app.route('/users/register', methods=['POST'])
def register_user():
    data = request.get_json()
    data['id'] = None
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify(status='SUCCESS', message='Registered successfully'), 201


# database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


user_schema = UserSchema()
users_schema = UserSchema(many=True)


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


class ProductSchema(ma.Schema):
    class Meta:
        fields = (
            'product_id',
            'product_name',
            'product_description',
            'product_price_currency',
            'product_price',
            'product_discount_percent',
            'product_vat_percent',
            'created_at',
            'last_updated_at',
            'product_markup_percent'
        )


product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


if __name__ == '__main__':
    app.run()
