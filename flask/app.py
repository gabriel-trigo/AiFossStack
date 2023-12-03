from flask import Flask, g, render_template, request, redirect, url_for, session
from sqlalchemy import text
from flask_mysqldb import MySQL
import pickle

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'lkUig57Yh!@'
app.config['MYSQL_DB'] = 'llama'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.secret_key = 'your_secret_key'

mysql = MySQL(app)

@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request.

    The variable g is globally accessible.
    """
    try:
        g.curr = mysql.connection.cursor()
        print("opened")
    except:
        print("uh oh, problem connecting to database")
        import traceback; traceback.print_exc()
        g.curr = None

@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    try:
        g.curr.close()
        print("closed")
    except Exception as e:
        pass



def get_db():
    return g.curr



@app.route("/")
def index():
    db = get_db()
    context = {}
    return render_template("base.html", **context)



@app.route("/authenticate", methods=["POST"])
def authenticate():
    email = request.form.get("email")
    password = request.form.get("password")
    print(is_authenticated(email, password))
    res = is_authenticated(email, password) != None
    if res:
        return { "result": "success" }
    return { "result": "fail" }



def is_authenticated(email, password):
    db = get_db()
    db.execute(
        "SELECT * FROM users WHERE email = %(email)s",
        {"email": email}
    )
    user = db.fetchone()

    print(user["password"])
     
    if user:
        if user["password"]==password:
            return user
    return None



@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = is_authenticated(email, password)  # Getting the user object
        if user:
            # Assuming 'username' is the user's username field in your database
            # Add any other user info you need to maintain context
            session["email"] = email
            return redirect(url_for("index"))
        else:
            error_message = "Invalid credentials. Please try again."

    return render_template("login.html", error_message=error_message)





@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))




def create_user(email, password):
    db = get_db()
    db.execute(
        "INSERT INTO users (email, password) VALUES (%(email)s, %(password)s)",
        {"email": email, "password": password}
    )
    mysql.connection.commit()
     



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")


        # Check if the username already exists
        db = get_db()
        db.execute(
            "SELECT * FROM users WHERE email = %(email)s",
            { "email": email }
        )
        existing_user = db.fetchone()

        if existing_user:
            error_message = "Email already exists. Please choose a different one."
        else:
            create_user(email, password)
            session["email"] = email
            return redirect(url_for("index"))

    return render_template("signup.html", error_message=error_message if "error_message" in locals() else None)



@app.route("/save_model", methods=["POST"])
def save_model():
    # Authenticate
    db = get_db()
    email = request.form.get("email")
    password = request.form.get("password")
    if not is_authenticated(email, password): return

    model_name = request.form.get("model_name")
    index_file = request.form.get("model_str")
    index_file = request.files['model_str'].read()
    print(index_file[:10])
    try:
        db.execute("""
                    INSERT INTO indexes(email, model_name, index_file)
                    VALUES (%(email)s, %(model_name)s, %(index_file)s)
                    """, 
                    {
                        "email": email,
                        "model_name": model_name,
                        "index_file": index_file
                    })
        mysql.connection.commit()
    
    except Exception:
        return { "status": "failed" }

    return { "status": "success" }



@app.route("/get_account_models", methods=["POST"])
def get_account_models():
    # Authenticate
    db = get_db()
    email = request.form.get("email")
    password = request.form.get("password")
    if not is_authenticated(email, password): return
    try:
        db.execute("""
                    SELECT model_name FROM indexes
                    WHERE email = %(email)s
                    """, 
                    {
                        "email": email
                    })
    
    except Exception:
        return { "status": "failed" }
    return { "models": db.fetchall() }



@app.route("/get_model", methods=["POST"])
def get_model():
    # Authenticate
    db = get_db()
    email = request.form.get("email")
    password = request.form.get("password")
    if not is_authenticated(email, password): return

    model_name = request.form.get("model_name")
    
    try:
        db.execute("""
                    SELECT * FROM indexes
                    WHERE email = %(email)s AND model_name = %(model_name)s
                    """, 
                    {
                        "email": email,
                        "model_name": model_name,
                    })
        result = db.fetchone()
    except Exception:
        return { "status": "failed" }
    print(result["index_file"][:10])
    return result["index_file"]
