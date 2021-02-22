from flask import Flask, jsonify, send_file
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
db_filename = os.path.join(basedir, 'invoice_system.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_filename
# app.config['SQLALCHEMY_ECHO'] = True

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


if __name__ == '__main__':
    app.run()
