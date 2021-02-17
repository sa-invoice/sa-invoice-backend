from datetime import datetime
from uuid import uuid4
from flask import jsonify, request, Blueprint
from .models import db, Product
from .schemas import product_schema, products_schema


products_api = Blueprint('products_api', __name__)


def insert_product(**args):
    args['product_id'] = uuid4().hex
    args['created_at'] = None
    args['last_updated_at'] = None
    product = Product(**args)
    db.session.add(product)
    db.session.commit()
    return product


@products_api.route('', methods=['GET'])
def get_products():
    query_result = db.session.query(Product).all()
    products_list = products_schema.dump(query_result)
    return jsonify(products_list)


def get_product_by_id(product_id: str):
    return Product.query.filter_by(product_id=product_id).first()


@products_api.route('<product_id>', methods=['PUT'])
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


@products_api.route('<product_id>', methods=['GET'])
def get_product_details(product_id: str):
    row = get_product_by_id(product_id)
    if row:
        return jsonify(product_schema.dump(row)), 200
    else:
        return jsonify(error_code='PRODUCT_NOT_FOUND', message='Product not found!'), 404


@products_api.route('', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        product = insert_product(**data)
        product = product_schema.dump(product)
        return jsonify(status='SUCCESS', message='Product added successfully!', added_product=product), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(status='ERROR', errors=e.args), 400