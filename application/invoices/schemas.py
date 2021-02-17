from flask_marshmallow import Schema
from marshmallow import fields


class InvoiceItemSchema(Schema):
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


class InvoiceSchema(Schema):
    invoice_id = fields.String()
    invoice_number = fields.Integer()
    invoice_items = fields.List(fields.Nested(InvoiceItemSchema(exclude=('invoice_id',))))
    created_at = fields.DateTime()
    invoice_gross_amount = fields.Float()
    total_discount_amount = fields.Float()
    total_tax_amount = fields.Float()
    invoice_net_amount = fields.Float()
    client_name = fields.String()
    client_tin = fields.String()
    client_address = fields.String()
    client_city = fields.String()
    is_client_taxable = fields.Boolean()


invoice_schema = InvoiceSchema()
invoices_schema = InvoiceSchema(many=True)