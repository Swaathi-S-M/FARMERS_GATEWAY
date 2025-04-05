from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from supabase import create_client, Client
import requests
from io import BytesIO
import tensorflow as tf
from PIL import Image 
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import preprocess_input
import numpy as np
import qrcode

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # Secret Key for session handling

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Fetch form data
        name = request.form.get('name')
        email = request.form.get('email')
        password = generate_password_hash(request.form.get('password'))
        mobile = request.form.get('mobile')
        role = request.form.get('role')
        latitude = request.form.get('latitude')  
        longitude = request.form.get('longitude')

        # Fetch max ID from Supabase
        response = supabase.table("newuser").select("id").order("id", desc=True).limit(1).execute()

        print("Fetch ID Response:", response)  # Debugging line to log the response

        if response.data:
            max_id = response.data[0]['id']  
            next_id = max_id + 1
        else:
            next_id = 1 

        try:
            # Insert user into Supabase
            insert_response = supabase.table("newuser").insert({
                "id": next_id,
                "name": name,
                "email": email,
                "password": password,
                "mobile_no": mobile,
                "role": role,
                "latitude": latitude if latitude else None,  
                "longitude": longitude if longitude else None  
            }).execute()

            print("Insert Response:", insert_response)  # Log the insert response

            if insert_response.data:  # Check if data was successfully inserted
                print("Registration successful, redirecting to login page.")
                return redirect(url_for('login'))  # Redirect to login page after successful registration
            else:
                print(f"Error inserting data: {insert_response}")
                return render_template('register.html', error="Failed to insert data into the database.")
        except Exception as e:
            print("Error inserting data:", str(e))  # Log any exception during insert
            return render_template('register.html', error="Failed to insert data.")

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Query the user by email from Supabase
        response = supabase.table('newuser').select('id', 'email', 'password').eq('email', email).execute()

        if response.data:
            # Check if the password matches
            user = response.data[0]
            if check_password_hash(user['password'], password):
                # Store user email in session
                session['user'] = user['email']
                return redirect(url_for('location_page'))  # Redirect to location page
            else:
                return render_template('login.html', error="Invalid credentials")
        else:
            return render_template('login.html', error="User not found")

    return render_template('login.html')


@app.route('/location')
def location_page():
    if 'user' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in
    return render_template('location.html')


@app.route('/map')
def map_view():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('map.html')


# Endpoint to receive and store user's current location (latitude, longitude)
@app.route('/update_location', methods=['POST'])
def update_location():
    if 'user' not in session:
        return jsonify({"message": "User not logged in"}), 403

    data = request.get_json()

    # Debugging: Print received data
    print("Received Data:", data)

    email = session.get('user')
    if not email:
        return jsonify({"message": "User not found"}), 404

    lat = data.get('lat')
    lng = data.get('lng')

    # Debugging: Check if lat/lng is received
    print(f"Updating for {email}: lat={lat}, lng={lng}")

    if lat is None or lng is None:
        return jsonify({"message": "Invalid latitude or longitude"}), 400

    try:
        # Update location in Supabase
        response = supabase.table('newuser').update({
            'latitude': lat,
            'longitude': lng
        }).eq('email', email).execute()

        # Debugging: Check Supabase response
        print("Supabase Response:", response)

        return jsonify({"message": "Location updated successfully"}), 200

    except Exception as e:
        print("Error updating location:", e)
        return jsonify({"message": f"Error: {str(e)}"}), 500



@app.route('/options')
def options():
    if 'user' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('options.html')

@app.route('/disease_detection')
def disease_detection():
    return render_template('img.html')


MODEL_PATH = "models/plantmodel.h5"
IMG_SIZE = (224, 224)  # Image size used during training

# Load the trained model
model = tf.keras.models.load_model(MODEL_PATH,compile=False)



# Define class names
class_names = [
    'Apple__Apple_scab', 'Apple_Black_rot', 'Apple_Cedar_apple_rust', 'Apple_healthy',
    'Blueberry_healthy', 'Cherry(including_sour)__Powdery_mildew', 'Cherry(including_sour)__healthy',
    'Corn(maize)__Cercospora_leaf_spot Gray_leaf_spot', 'Corn(maize)__Common_rust',
    'Corn_(maize)__Northern_Leaf_Blight', 'Corn(maize)__healthy', 'Grape_Black_rot',
    'Grape_Esca(Black_Measles)', 'Grape__Leaf_blight(Isariopsis_Leaf_Spot)', 'Grape__healthy',
    'Orange_Haunglongbing(Citrus_greening)', 'Peach__Bacterial_spot', 'Peach_healthy',
    'Pepper,_bell_Bacterial_spot', 'Pepper,_bell_healthy', 'Potato_Early_blight',
    'Potato_Late_blight', 'Potato_healthy', 'Raspberry_healthy', 'Soybean_healthy',
    'Squash_Powdery_mildew', 'Strawberry_Leaf_scorch', 'Strawberry_healthy',
    'Tomato_Bacterial_spot', 'Tomato_Early_blight', 'Tomato_Late_blight', 'Tomato_Leaf_Mold',
    'Tomato_Septoria_leaf_spot', 'Tomato_Spider_mites Two-spotted_spider_mite',
    'Tomato_Target_Spot', 'Tomato_Tomato_Yellow_Leaf_Curl_Virus', 'Tomato_Tomato_mosaic_virus',
    'Tomato__healthy'
]

# Plant Disease Detection route
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the uploaded file
        file = request.files['image']  # Use the 'image' field from your form
        if file:
            try:
                # Open the image file directly with PIL
                img = Image.open(file.stream)  # Use the stream to read the uploaded file
                img = img.resize(IMG_SIZE)  # Resize the image to match model's expected size
                
                # Convert image to numpy array for model
                img_array = image.img_to_array(img)  # Use the 'image' module from TensorFlow
                img_array = np.expand_dims(img_array, axis=0)  # Expand dims for batch size (1)
                
                # Preprocess the image for the model (VGG16 specific preprocessing in this case)
                img_array = preprocess_input(img_array)  # This prepares the image as required by VGG16
                
                # Make prediction
                predictions = model.predict(img_array)
                predicted_class = np.argmax(predictions, axis=1)[0]
                predicted_class_name = class_names[predicted_class]
                
                # Render the result template with prediction result
                return render_template('result.html', result=predicted_class_name, image_path=file.filename)
            
            except Exception as e:
                print(f"Error: {e}")
                return f"Error processing the image: {e}"

    return render_template('img.html')  # Return to the image input page if not a POST request

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    
            
    return render_template('sell.html',user_id=session.get('user_id'))




    
    
@app.route('/submit_order', methods=['POST'])
def submit_order():
    if 'user' not in session:
        return jsonify({"message": "User not logged in"}), 403

    data = request.get_json()
    email = session.get('user')

    user_response = supabase.table('newuser').select('name', 'latitude', 'longitude').eq('email', email).execute()

    if not user_response.data:
        return jsonify({"message": "User not found in database"}), 404

    user_info = user_response.data[0]
    user_name = user_info['name']
    latitude = user_info['latitude']
    longitude = user_info['longitude']
    upi_id = data.get("upi_id")  # 🟢 Fetch UPI ID from the request

    order_entries = []
    for order in data["orders"]:
        price_per_kg = float(order["total_price"]) / int(order["quantity"])  # Calculate price per kg

        order_entries.append({
            "name": user_name,
            "product": order["product"],
            "quantity": int(order["quantity"]),
            "sell_price": round(price_per_kg),  # Store price per kg instead of total price
            "latitude": latitude,
            "longitude": longitude,
            "upi_id": upi_id  # 🟢 Store UPI ID in the order
        })

    insert_response = supabase.table("Order").insert(order_entries).execute()

    if insert_response.data:
        return jsonify({"message": "Order submitted successfully", "redirect": url_for('sell_map')})
    else:
        return jsonify({"message": "Error submitting order"}), 500

@app.route('/get_sellers')
def get_sellers():
    response = supabase.table('Order').select("name, latitude, longitude, product, quantity, sell_price").execute()
    
    if not response.data:
        return jsonify([])

    return jsonify(response.data)

@app.route('/sell_map')
def sell_map():
    return render_template('sell_map.html')

@app.route('/pmap')
def purchase_map():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('pmap.html')

@app.route('/purchase_page')
def purchase_page():
    return render_template('purchase_page.html')
@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.get_json()
    seller_name = data.get('seller')
    product = data.get('product')
    quantity = int(data.get('quantity'))

    # Fetch the current quantity
    seller_data = supabase.table("Order") \
        .select("id, quantity") \
        .eq("name", seller_name).eq("product", product) \
        .order("id", desc=True).limit(1).execute()

    if not seller_data.data:
        return jsonify({"message": "Seller not found", "success": False})

    seller_entry = seller_data.data[0]
    new_quantity = seller_entry['quantity'] - quantity

    if new_quantity < 0:
        return jsonify({"message": "Not enough quantity available", "success": False})

    supabase.table("Order").update({"quantity": new_quantity}).eq("id", seller_entry['id']).execute()

    return jsonify({"message": "Order placed successfully", "success": True})

import base64
@app.route('/get_upi_qr')
def get_upi_qr():
    seller = request.args.get('seller')
    amount = request.args.get('amount')  # Get amount from query parameter

    if not amount:
        return jsonify({"success": False, "error": "Amount is required"}), 400

    # Fetch UPI ID from Supabase
    response = supabase.table("Order").select("upi_id").eq("name", seller).execute()
    if not response.data or "upi_id" not in response.data[0]:
        return jsonify({"success": False, "error": "UPI ID not found for seller"}), 404

    upi_id = response.data[0]["upi_id"]

    # Construct UPI payment URI with amount
    upi_link = f"upi://pay?pa={upi_id}&pn={seller}&am={amount}&cu=INR"

    # Generate QR Code
    qr = qrcode.make(upi_link)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    return jsonify({
        "success": True,
        "upi_id": upi_id,
        "qr_url": f"data:image/png;base64,{qr_b64}"
    })





@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


