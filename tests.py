import os
import unittest

from app import app, basedir
from application import db


class AppTest(unittest.TestCase):

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'invoice_tests.db')
        db.init_app(app)
        with app.app_context():
            db.create_all()
        self.test_client = app.test_client(self)

    def tearDown(self):
        os.unlink(os.path.join(basedir, 'invoice_tests.db'))
        pass

    def test_index(self):
        response = self.test_client.get('/')
        status_code = response.status_code
        self.assertEqual(status_code, 404)


if __name__ == '__main__':
    unittest.main()
