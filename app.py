from flask import Flask, jsonify, request

app = Flask(__name__)

from products import products

@app.route('/ping')
def ping():
    return jsonify({'message': 'Pong!'})

@app.route('/products')
def get_products():
    return jsonify(products)

@app.route('/products/<string:product_name>')
def get_product_by_name(product_name):
    founded = [product for product in products if product['name'] == product_name]
    if len(founded) > 0: 
        return jsonify(founded[0])
    else:
        # return jsonify({'message', 'Product not found'})
        return "Not Found", 404

@app.route('/products', methods=['POST'])
def post_product():
    new_product = {
        "name": request.json['name'],
        "price": request.json['price'],
        'quantity': int(request.json['quantity'])
    }
    products.append(new_product)
    return jsonify(products)

if __name__ == "__main__":
    app.run(debug=True, port=4000)