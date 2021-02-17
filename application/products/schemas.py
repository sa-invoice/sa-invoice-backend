from flask_marshmallow import Schema


class ProductSchema(Schema):
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
