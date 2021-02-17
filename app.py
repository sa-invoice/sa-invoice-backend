from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import event
import os
from flask_marshmallow import Marshmallow
from sqlalchemy.engine import Engine
from application import db
from application.clients.routes import clients_api, insert_client
from application.invoices.routes import invoices_api
from application.products.routes import products_api, insert_product

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'invoice_system.db')

db.init_app(app)
ma = Marshmallow(app)
CORS(app)

app.register_blueprint(clients_api, url_prefix='/api/clients')
app.register_blueprint(products_api, url_prefix='/api/products')
app.register_blueprint(invoices_api, url_prefix='/api/invoices')


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
    insert_product(
        product_name='Designing',
        product_description='Design various stuff',
        product_price=50,
        product_vat_percent=5
    )
    insert_client(
        client_name='Alpha Tech',
        client_tin='82375628378',
        client_address='Somewhere on the earth',
        client_city='Jedda',
        is_client_taxable=True
    )
    insert_client(
        client_name='Beta Tech',
        client_tin='82375628379',
        client_address='Somewhere on the earth',
        client_city='Bangalore',
        is_client_taxable=False
    )
    print('Database seeded!')


if __name__ == '__main__':
    app.run()
