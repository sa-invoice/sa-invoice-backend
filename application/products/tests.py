import unittest

from app import app
from tests import AppTest


class ProductsTest(AppTest):

    def setUp(self):
        super().setUp()
        self.prefix = '/api/products'

    def create_product(self):
        return self.test_client.post(f'{self.prefix}', json={
            "product_description": "Design various stuffs",
            "product_discount_percent": 0.0,
            "product_markup_percent": 20.0,
            "product_name": "Designing",
            "product_price": 30.0,
            "product_price_currency": "SAR",
            "product_vat_percent": 3.0
        })

    def get_product_by_id(self, product_id):
        return self.test_client.get(f'{self.prefix}/{product_id}')

    def test_index(self):
        response = self.test_client.get(f'{self.prefix}')
        status_code = response.status_code
        self.assertEqual(status_code, 200)

    def test_create_product(self):
        response = self.create_product()
        self.assertEqual(response.status_code, 201)
        product_id = response.get_json()['added_product']['product_id']
        response = self.get_product_by_id(product_id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['product_id'], product_id)

    def test_update_product(self):
        description = 'UPDATED_DESCRIPTION'
        product_id = self.create_product().get_json()['added_product']['product_id']
        response = self.test_client.put(f'{self.prefix}/{product_id}', json={
            "product_description": description
        })
        self.assertEqual(response.status_code, 200)
        response = self.get_product_by_id(product_id)
        self.assertEqual(response.get_json()['product_description'], description)

    def test_product_id_cannot_be_updated(self):
        product_id = self.create_product().get_json()['added_product']['product_id']
        random_id = 'SOME_RANDOM_ID'
        self.test_client.put(f'{self.prefix}/{product_id}', json={
            "product_id": random_id
        })
        response = self.get_product_by_id(random_id)
        self.assertEqual(response.status_code, 404)
        response = self.get_product_by_id(product_id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['product_id'], product_id)
