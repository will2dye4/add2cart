import json
import os

from flask import Flask, request    #, session, g, redirect, url_for, abort, render_template, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    SQLALCHEMY_DATABASE_URI='sqlite:///%s' % os.path.join(app.root_path, 'add2cart.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    SECRET_KEY='development_key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('ADD2CART_SETTINGS', silent=True)

db = SQLAlchemy(app)

DEFAULT_GROCERIES = {
    'Bakery': ['bread'],
    'Cleaning Supplies': ['paper towels', 'soap'],
    'Dairy': ['cheese', 'milk', 'yogurt'],
    'Deli': ['sandwich'],
    'Dry Goods': ['chicken broth'],
    'Frozen Goods': ['ice cream'],
    'Meats': ['boneless skinless chicken breast', 'pork tenderloin'],
    'Produce': ['onions', 'fresh thyme', 'watermelon'],
    'Seafood': ['shrimp']
}
DEFAULT_QUANTITY_TYPES = ['bag', ('box', 'boxes'), 'can', 'cup', 'jar', ('lb.', 'lbs.'), 'package']


class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Category(name=%r)' % self.name


class QuantityType(db.Model):
    quantity_type_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    plural_name = db.Column(db.String, nullable=True)

    def __init__(self, name, plural_name=None):
        self.name = name
        if plural_name is None:
            plural_name = name + 's'
        self.plural_name = plural_name

    def __repr__(self):
        return 'QuantityType(name=%r,plural_name=%r)' % (self.name, self.plural_name)


class GroceryType(db.Model):
    grocery_type_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=True)
    default_quantity_type_id = db.Column(db.Integer, db.ForeignKey('quantity_type.quantity_type_id'), nullable=True)
    category = db.relationship('Category', backref=db.backref('grocery_types'))
    default_quantity_type = db.relationship('QuantityType')

    def __init__(self, name, category=None, default_quantity_type=None):
        self.name = name
        self.category = category
        self.default_quantity_type = default_quantity_type

    def __repr__(self):
        return 'GroceryType(name=%r,category=%r,default_quantity_type=%r)' % \
               (self.name, self.category, self.default_quantity_type)


class ShoppingList(db.Model):
    shopping_list_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True)

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return 'ShoppingList(name=%r)' % self.name


class ListItem(db.Model):
    shopping_list_id = db.Column(db.Integer, db.ForeignKey('shopping_list.shopping_list_id'), primary_key=True)
    grocery_type_id = db.Column(db.Integer, db.ForeignKey('grocery_type.grocery_type_id'), primary_key=True)
    quantity_type_id = db.Column(db.Integer, db.ForeignKey('quantity_type.quantity_type_id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    shopping_list = db.relationship('ShoppingList', backref=db.backref('items'))
    grocery_type = db.relationship('GroceryType')
    quantity_type = db.relationship('QuantityType')

    def __init__(self, shopping_list, grocery_type, quantity_type=None, quantity=None):
        self.shopping_list = shopping_list
        self.grocery_type = grocery_type
        self.quantity_type = quantity_type
        self.quantity = quantity

    def __repr__(self):
        return 'ListItem(shopping_list=%r,grocery_type=%r,quantity_type=%r,quantity=%r)' % \
               (self.shopping_list, self.grocery_type, self.quantity_type, self.quantity)


@app.route('/')
def index():
    shopping_list = ShoppingList.query.first()
    return json.dumps({'list_name': shopping_list.name, 'items': [item.grocery_type.name for item in shopping_list.items]})


def create_default_data():
    for category_name, groceries in DEFAULT_GROCERIES.iteritems():
        category = Category(category_name)
        db.session.add(category)
        db.session.add_all([GroceryType(grocery, category) for grocery in groceries])
    for quantity_type in DEFAULT_QUANTITY_TYPES:
        if isinstance(quantity_type, tuple):
            db.session.add(QuantityType(*quantity_type))
        else:
            db.session.add(QuantityType(quantity_type))
    db.session.commit()


if __name__ == '__main__':
    # db.drop_all()
    # db.create_all()
    # create_default_data()
    app.run()
