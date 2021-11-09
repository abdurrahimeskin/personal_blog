from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
# Creating Flask App
app = Flask(__name__)
# for flask messages
app.secret_key = "aeblog"
# MySQL Configurations
app.config["MYSQL_HOST"] = "127.0.0.1"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "aeblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

# connecting the app to mySQL
mysql = MySQL(app)

# user login decorator


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login to view that page", "danger")
            return redirect(url_for("login"))
    return decorated_function

# user signing up from


class RegisterForm(Form):
    name = StringField("Name Surname", validators=[
                       validators.Length(min=4, max=25)])
    username = StringField("Username", validators=[
                           validators.Length(min=5, max=35)])
    email = StringField("Email Address", validators=[
                        validators.Email(message="Please enter validate password")])
    password = PasswordField("Password", validators=[validators.DataRequired(
        message="Please enter your password "), validators.EqualTo(fieldname="confirm", message="Passwords didn't fetch")])
    confirm = PasswordField("Password Validation")

# user login form


class LoginForm(Form):
    username = StringField("Username")
    password = PasswordField("Password")

# article form


class ArticleForm(Form):
    title = StringField("Article Title", validators=[
                        validators.length(min=5, max=100)])
    content = TextAreaField("Article Content", validators=[
                            validators.length(min=10, max=1000)])


# main page
@app.route('/')
def index():

    return render_template("index.html")

# about page


@app.route('/about')
def about():
    return render_template("about.html")

# dashboard page


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM ARTICLES WHERE AUTHOR= %s"
    result = cursor.execute(query, (session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")

# register page


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.name.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        query = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(query, (name, email, username, password))
        mysql.connection.commit()
        cursor.close()
        flash("Kayıt olundu", "success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)

# login page


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()

        query = "select * from users where username = %s"
        validation = cursor.execute(query, (username,))
        if validation > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Login Accepted", "success")
                # session start
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Wrong password", "danger")
                return redirect(url_for("login"))
        else:
            flash("No user has been found ", "danger")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)

# log out


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# creating article


@app.route("/addarticle", methods=["GET", "POST"])
def addaticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        query = "INSERT INTO ARTICLES(TITLE,AUTHOR,CONTENT) VALUES(%s,%s,%s)"
        cursor.execute(query, (title, session["username"], content))
        mysql.connection.commit()
        cursor.close()
        flash("Article has been created", "success")
        return redirect(url_for("dashboard"))
    return render_template("addarticles.html", form=form)

# articles page


@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM ARTICLES"
    result = cursor.execute(query)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")
# article detail page


@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM ARTICLES WHERE ID= %s"
    result = cursor.execute(query, (id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")

# updating articles


@app.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM ARTICLES WHERE AUTHOR = %s AND ID = %s"
        result = cursor.execute(query, (session["username"], id))
        if result == 0:
            flash("No article has been found or access denied", "danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form=form)

    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        cursor = mysql.connection.cursor()
        query = "UPDATE ARTICLES SET TITLE= %s, CONTENT= %s WHERE ID= %s"
        cursor.execute(query, (newTitle, newContent, id))
        mysql.connection.commit()
        cursor.close()
        flash("Article has been updated", "success")
        return redirect(url_for("dashboard"))


# deleting articles


@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM ARTICLES WHERE AUTHOR = %s AND ID = %s"
    result = cursor.execute(query, (session["username"], id))
    if result > 0:
        query_2 = "DELETE FROM ARTICLES WHERE ID = %s"
        cursor.execute(query_2, (id,))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("dashboard"))
    else:
        flash("Access denied or article does not exist", "danger")
        return redirect(url_for("index"))

# Search Page


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM ARTICLES WHERE TITLE LIKE '%"+keyword+"%'"
        result = cursor.execute(query)
        if result == 0:
            flash("No articles has been found", "danger")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles=articles)


if __name__ == "__main__":
    app.run(debug=True)
