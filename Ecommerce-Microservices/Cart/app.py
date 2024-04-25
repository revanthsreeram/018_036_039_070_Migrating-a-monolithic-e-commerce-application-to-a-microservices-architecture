from flask import Flask, jsonify, render_template, request
import pymongo.errors

app = Flask(__name__)
MONGO_URI = "mongodb+srv://arevanthsreeram:Dg4eP6YcuClsxTf9@cluster0.lgmqzy1.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(MONGO_URI)
db = client.get_database('ecommerce')

@app.route("/")
def hello():
    return jsonify("Welcome to cart")

@app.route('/check')
def check():
    a = 0
    try:
        db.command('ping')
        print("MongoDB Connection Successful!")
        a = 1
    except pymongo.errors.ConnectionFailure:
        print("MongoDB Connection Failed!")
    return jsonify(a)

# Add a product to the cart
@app.route('/cart', methods=['POST'])
def add_to_cart():
    carts = db.carts
    data = request.get_json()
    userid = data.get('userid')
    product_name = data.get('productname')
    quantity = data.get('quantity')

    # Fetch the product details from the products collection
    products = db.products
    product = products.find({"name": product_name})

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Check if the user has an existing cart
    cart = carts.find_one({'userid': userid})

    if not cart:
        # Create a new cart for the user
        cart = {
            'userid': userid,
            'products': [
                {
                    'productid': str(product["productid"]),
                    'name': product["name"],
                    'quantity': quantity
                }
            ]
        }
        carts.insert_one(cart)
    else:
        # Add the product to the existing cart
        existing_product = next((p for p in cart['products'] if p['productid'] == str(product['_id'])), None)
        if existing_product:
            existing_product['quantity'] += quantity
        else:
            cart['products'].append({
                'productid': str(product['_id']),
                'name': product['name'],
                'quantity': quantity
            })
        carts.update_one({'userid': userid}, {'$set': {'products': cart['products']}})

    return jsonify({'message': 'Product added to cart'}), 200

# Get the cart for a user
@app.route('/cart/<int:userid>', methods=['GET'])
def get_cart(userid):
    carts = db.carts
    cart = carts.find_one({'userid': userid}, {'_id': 0})
    if cart:
        return jsonify(cart)
    else:
        return jsonify({'error': 'Cart not found'}), 404

# Update the quantity of a product in the cart
@app.route('/cart/<int:userid>/<product_name>', methods=['PUT'])
def update_cart(userid, product_name):
    carts = db.carts
    data = request.get_json()
    quantity = data.get('quantity')

    cart = carts.find_one({'userid': userid})
    if not cart:
        return jsonify({'error': 'Cart not found'}), 404

    product_found = False
    for product in cart['products']:
        if product['name'] == product_name:
            product['quantity'] = quantity
            product_found = True
            break

    if not product_found:
        return jsonify({'error': 'Product not found in cart'}), 404

    carts.update_one({'userid': userid}, {'$set': {'products': cart['products']}})
    return jsonify({'message': 'Cart updated'}), 200

# Remove a product from the cart
@app.route('/cart/<int:userid>/<product_name>', methods=['DELETE'])
def remove_from_cart(userid, product_name):
    carts = db.carts

    cart = carts.find_one({'userid': userid})
    if not cart:
        return jsonify({'error': 'Cart not found'}), 404

    cart['products'] = [p for p in cart['products'] if p['name'] != product_name]

    if not cart['products']:
        # If the cart is empty, remove the cart document
        carts.delete_one({'userid': userid})
    else:
        carts.update_one({'userid': userid}, {'$set': {'products': cart['products']}})

    return jsonify({'message': 'Product removed from cart'}), 200

# Route to render the HTML template
@app.route('/view_cart')
def view_cart():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5004, debug=True)