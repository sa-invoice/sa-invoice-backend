import os
from datetime import datetime
from uuid import uuid4

import jinja2
from flask import jsonify, request, Blueprint
from pdfkit import pdfkit

from definitions import ROOT_DIR
from .models import Client
from .schemas import client_schema, clients_schema
from application import db

clients_api = Blueprint('clients_api', __name__)


def insert_client(**args):
    args['client_id'] = uuid4().hex
    args['created_at'] = None
    args['last_updated_at'] = None
    client = Client(**args)
    db.session.add(client)
    db.session.commit()
    return client


def get_client_by_id(client_id: str):
    return Client.query.filter_by(client_id=client_id).first()


@clients_api.route('', methods=['POST'])
def add_client():
    try:
        data = request.get_json()
        client = insert_client(**data)
        return jsonify(status='SUCCESS', message='Client added successfully!', added_client=client_schema.dump(client)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(status='ERROR', errors=e.args), 400


@clients_api.route('', methods=['GET'])
def get_clients():
    try:
        query_result = Client.query.all()
        clients_list = clients_schema.dump(query_result)
        return jsonify(clients_list)
    except Exception as e:
        return jsonify(status='ERROR', errors=e.args), 400


@clients_api.route('<client_id>', methods=['GET'])
def get_client_details(client_id: str):
    try:
        row = get_client_by_id(client_id)
        if row:
            return jsonify(client_schema.dump(row)), 200
        else:
            return jsonify(error_code='CLIENT_NOT_FOUND', message='Client not found!'), 404
    except Exception as e:
        return jsonify(status='ERROR', errors=e.args), 400


@clients_api.route('<client_id>', methods=['PUT'])
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
