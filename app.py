from flask import Flask, render_template, request, redirect, url_for, flash, jsonify  # Add jsonify here
from decimal import Decimal
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host='localhost',
        database='Loans_CDP',
        user='postgres',
        password='P@Ss2890'
    )
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        
        # Validate customer ID
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM loans_pricing WHERE customer_id = %s;", (customer_id,))
        customer = cur.fetchone()
        cur.close()
        conn.close()
        
        if customer:
            return redirect(url_for('loan_details', customer_id=customer_id))
        else:
            flash('Customer ID does not exist. Please try again.', 'error')

    return render_template('index.html')

@app.route('/loan_details/<customer_id>', methods=['GET', 'POST'])
def loan_details(customer_id):
    if request.method == 'POST':
        # Capture loan details
        annual_earnings = request.form['earnings']
        monthly_expenses = request.form['spends']
        monthly_rental = request.form['rental']
        dependents = request.form['dependents']
        marital_status = request.form['maritalStatus']

        # Store loan details and redirect to loan purpose page
        return redirect(url_for('loan_purpose_view', customer_id=customer_id, annual_earnings=annual_earnings,
                                monthly_expenses=monthly_expenses, monthly_rental=monthly_rental,
                                dependents=dependents, marital_status=marital_status))

    return render_template('loan_details.html', customer_id=customer_id)

@app.route('/loan_purpose/<customer_id>', methods=['GET', 'POST'])
def loan_purpose_view(customer_id):
    if request.method == 'POST':
        loan_purpose = request.form['loan_purpose']  # Capture loan purpose
        loan_amount = int(request.form['loan_amount'])  # Convert loan_amount to float

        # Fetch pricing details from loans_pricing table
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT offerlowband1, offerhighband1, offerapr1,
                   offerlowband2, offerhighband2, offerapr2,
                   offerlowband3, offerhighband3, offerapr3,
                   tenure
            FROM loans_pricing;
        """)
        pricing = cur.fetchone()
        cur.close()
        conn.close()

        if pricing:
            # Unpack pricing details
            (offerlowband1, offerhighband1, offerapr1,
             offerlowband2, offerhighband2, offerapr2,
             offerlowband3, offerhighband3, offerapr3,
             tenure) = pricing

            # Initialize quote details
            quote_details = {}

            # Check which band the loan amount falls into
            if offerlowband1 <= loan_amount <= offerhighband1:
                quote_details = {
                    'Loan Amount': loan_amount,
                    'APR': offerapr1,
                    'Tenure': tenure,
                    'Loan Purpose': loan_purpose  # Include loan purpose
                }
            elif offerlowband2 <= loan_amount <= offerhighband2:
                quote_details = {
                    'Loan Amount': loan_amount,
                    'APR': offerapr2,
                    'Tenure': tenure,
                    'Loan Purpose': loan_purpose  # Include loan purpose
                }
            elif offerlowband3 <= loan_amount <= offerhighband3:
                quote_details = {
                    'Loan Amount': loan_amount,
                    'APR': offerapr3,
                    'Tenure': tenure,
                    'Loan Purpose': loan_purpose  # Include loan purpose
                }
            else:
                quote_details = {
                    'Error': 'The loan amount entered does not fall within any offer bands.'
                }

            # Render the loan quote page with the fetched details
            return render_template('loan_quote.html', quote_details=quote_details,customer_id=customer_id)

    return render_template('loan_purpose.html', customer_id=customer_id)

@app.route('/save_event', methods=['POST'])
def save_event():
    
    
    try:
        data = request.get_json()
        
        # Check if required data exists
        if not all(key in data for key in ['customer_id', 'loan_amount', 'apr', 'tenure']):
            return jsonify({"message": "Missing data in request", "success": False}), 400

        customer_id = data['customer_id']
        loan_amount = data['loan_amount']
        apr = data['apr']
        tenure = data['tenure']
        print(customer_id)
        
        # Save to aep_events table
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO aep_events (customer_id, loan_amount, apr, tenure, event_time)
            VALUES (%s, %s, %s, %s, NOW());
        """, (customer_id, loan_amount, apr, tenure))
        
        conn.commit()
        cur.close()
        conn.close()

        print("was here")
        
        return '', 204  # No Content
    except Exception as e:
        print(f"Error saving event: {e}")  # Log the error
        return jsonify({"message": "An error occurred while saving the event", "success": False}), 500

def query_for_new_offer(customer_id, loan_amount, current_apr):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Query to get all price points for the customer
        cursor.execute("""
            SELECT offerlowband1, offerhighband1, offerapr1,
                   offerlowband2, offerhighband2, offerapr2,
                   offerlowband3, offerhighband3, offerapr3
            FROM loans_pricing
            WHERE customer_id = %s;
        """, (customer_id,))

        offers = cursor.fetchone()
        conn.close()

        if not offers:
            return {"success": False}  # No offers found for the customer

        # Extract offers
        offerlowband1, offerhighband1, offerapr1 = offers[0:3]
        offerlowband2, offerhighband2, offerapr2 = offers[3:6]
        offerlowband3, offerhighband3, offerapr3 = offers[6:9]

        # Create a list of offers for easy comparison
        offers_list = [
            (offerapr1, offerlowband1, offerhighband1),
            (offerapr2, offerlowband2, offerhighband2),
            (offerapr3, offerlowband3, offerhighband3)
        ]

        best_offer = None
        closest_loan_amount = None

        # Calculate the threshold amounts
        lower_limit = loan_amount * 0.5  # -50% of loan_amount
        upper_limit = loan_amount * 2.0   # +100% of loan_amount

        # Check each offer
        for offerapr, offerlowband, offerhighband in offers_list:
            # Check if the APR is lower than the current APR
            if offerapr < current_apr:
                # Check if the offer's low and high bands are within the calculated limits
                if offerlowband <= upper_limit and offerhighband >= lower_limit:
                    # Calculate the distance from the loan_amount to offerlowband
                    distance = abs(loan_amount - offerlowband)
                    
                    # Select the closest offer
                    if best_offer is None or distance < closest_loan_amount:
                        best_offer = (offerapr, offerlowband, offerhighband)
                        closest_loan_amount = distance

        if best_offer:
            return {
                "success": True,  # Indicate that a new offer was found
                "new_loan_amount": best_offer[1],  # Return the best low band amount
                "new_apr": best_offer[0],
                "new_tenure": "60"  # Assuming tenure is fixed or can be fetched similarly
            }
        else:
            return {"success": False}  # No better offer found

    except Exception as e:
        print(f"Error querying database: {e}")  # Log the error
        return {"success": False}  # Return success as False in case of an error

@app.route('/get_new_offer', methods=['POST'])
def get_new_offer():
    data = request.json
    loan_amount = data.get('loan_amount')
    current_apr = data.get('apr')
    customer_id = data.get('customer_id')

    # Ensure loan_amount is an integer
    loan_amount = int(loan_amount)
    current_apr = Decimal(str(current_apr))

    # Check if loan_amount and apr are provided
    if loan_amount is None or current_apr is None:
        return jsonify({"message": "Loan amount and APR are required", "success": False}), 400

    # Query the database for a better loan offer
    new_offer = query_for_new_offer(customer_id, loan_amount, current_apr)
    
    if new_offer['success']:
        return jsonify(new_offer), 200
    else:
        return jsonify({"message": "No better offers available", "success": False}), 200

if __name__ == '__main__':
    app.run(debug=True)
