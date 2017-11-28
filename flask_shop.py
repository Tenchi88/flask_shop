import json

from flask import Flask, jsonify, render_template, url_for, redirect
from flask import request
from flask.views import View
from marshmallow import Schema, fields

from flask_bootstrap import Bootstrap

import db

app = Flask(__name__)
Bootstrap(app)
RATE_LIMITS_INFO = {}
MAX_REQUESTS_PER_USER = 100


class ProductSchema(Schema):
    title = fields.Str(required=True)
    price_rub = fields.Integer(required=True)
    product_image = fields.Str(required=False)
    in_store = fields.Boolean(defalt=False)
    params = fields.Str(required=True)


class CategorySchema(Schema):
    title = fields.Str(required=True)
    slug = fields.Str(required=True)
    is_visible = fields.Boolean(defalt=False)


class BaseView(View):
    validate_api_key = False
    validate_rate_limits = False

    def dispatch_request(self, **kwargs):
        self.session = db.Session()
        api_key = request.headers.get('HTTP-X-API-KEY')
        if self.validate_api_key and self.session.query(db.APIKeys.api_key).filter(db.APIKeys.api_key==api_key).exists():
            response = jsonify({'error': 'Wrong API key'})
            response.status_code = 400
            return response

        RATE_LIMITS_INFO[api_key] = RATE_LIMITS_INFO.get(api_key, 0) + 1
        if self.validate_rate_limits and RATE_LIMITS_INFO[api_key] > MAX_REQUESTS_PER_USER:
            response = jsonify({'error': 'Rate limit exceeded'})
            response.status_code = 400
            return response
        method_name = request.method.lower()
        return getattr(self, method_name)(**kwargs)


class ModelView(BaseView):
    model = None

    @property
    def all_model_fields(self):
        return [c.name for c in self.model.__table__.columns]


class ItemListResource(ModelView):
    schema = None
    search_field = None
    template = None

    def get(self):
        query = request.args.get('q')
        products_to_show = self.session.query(self.model)
        if query:
            products_to_show = products_to_show.filter(
                getattr(self.model, self.search_field).ilike('%{}%'.format(query)))

        filter_field = request.args.get('filter')
        if filter_field:
            products_to_show = [p for p in products_to_show if p.get(filter_field)]

        from_element = request.args.get('from')
        to_element = request.args.get('to')
        if from_element and to_element:
            from_element = int(from_element)
            to_element = int(to_element)
            products_to_show = products_to_show[from_element:to_element]

        fields = request.args.get('fields')
        if fields:
            fields = fields.split(',')
        else:
            fields = self.all_model_fields

        products = [p.to_dict(fields) for p in products_to_show]

        if self.template is not None:
            return render_template(self.template, products=products_to_show)
        return jsonify(products)

    def post(self):
        raw_product = json.loads(request.data.decode('utf-8'))
        clean_product, errors = self.schema().load(raw_product)
        if errors:
            response = jsonify(errors)
            response.status_code = 400
            return response

        self.session.add(self.model(**clean_product))
        self.session.commit()
        return jsonify(raw_product)


class ItemDetailResource(ModelView):
    schema = None
    template = None

    def get(self, product_id):
        product = self.session.query(self.model).filter(
            self.model.id == product_id
        ).first()
        if self.template is not None:
            return render_template(self.template, product=product)
        return jsonify(product.to_dict())

    def put(self, product_id):
        raw_product = json.loads(request.data.decode('utf-8'))
        clean_product, errors = self.schema().load(raw_product)
        if errors:
            response = jsonify(errors)
            response.status_code = 400
            return response
        product = self.session.query(self.model).filter(
            self.model.id==product_id
        ).first()
        for key, value in clean_product.items():
            setattr(product, key, value)
        self.session.add(product)
        self.session.commit()
        return jsonify('ok')

    def patch(self, product_id):
        raw_product = json.loads(request.data.decode('utf-8'))
        clean_product, errors = self.schema().load(raw_product, partial=tuple(fields))
        if errors:
            response = jsonify(errors)
            response.status_code = 400
            return response
        product = self.session.query(self.model).filter(
            self.model.id==product_id
        ).first()
        for key, value in clean_product.items():
            setattr(product, key, value)
        self.session.add(product)
        self.session.commit()
        return jsonify(product.to_dict())

    def delete(self, product_id):
        product = self.session.query(self.model).filter(
            self.model.id==product_id
        ).first()
        self.session.delete(product)
        self.session.commit()
        return jsonify('ok')


def add_rest_resource(app_, model_, schema_, search_field_, collection_name,
                      api_version=1,
                      template_detail=None,
                      template_list=None):
    class ProductsListView(ItemListResource):
        model = model_
        schema = schema_
        search_field = search_field_
        template = template_list

    class ProductsDetailView(ItemDetailResource):
        model = model_
        schema = schema_
        template = template_detail

    app_.add_url_rule(
        '/v%s/%s/' % (api_version, collection_name),
        view_func=ProductsListView.as_view('%s_list' % collection_name)
    )
    app_.add_url_rule(
        '/v%s/%s/<int:product_id>/' % (api_version, collection_name),
        view_func=ProductsDetailView.as_view('%s_detail' % collection_name),
        methods=['GET', 'PUT', 'PATCH', 'DELETE']
    )


add_rest_resource(app, db.Product, ProductSchema, 'title', 'products',
                  template_detail='products/detail_view.html',
                  template_list='products/list_view.html')
add_rest_resource(app, db.Category, CategorySchema, 'title', 'categories')


@app.route('/')
def index():
    return redirect(url_for('products_list'))


if __name__ == '__main__':
    app.run(debug=True)
