from flask_marshmallow import Schema


class ClientSchema(Schema):
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
