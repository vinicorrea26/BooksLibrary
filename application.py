import os
import requests

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#pagina inicialização
@app.route("/", methods=["GET"])
def index():
    session["user_id"] = []
    return render_template("index.html")

#formulario de criação de acesso
@app.route("/formulario", methods=["GET"])
def formulario():
    return render_template("formulario.html")

#validação de cadastro e cadastramento
@app.route("/cadsucess", methods=["POST"])
def cadsucess():
    if request.method =="POST":
        name=request.form.get("name")
        username=request.form.get("username")
        password=request.form.get("password")

        #procura se usuário já está cadastrado, se nao estiver realiza cadastro
        if db.execute("SELECT username FROM users WHERE username = :username",{"username": username}).rowcount == 0:
            db.execute("INSERT INTO users (name, username, password) VALUES (:name, :username, :password)", 
                        {"name": name, "username":username, "password":password})
            db.commit()
            return render_template("cadsucess.html", nome=name, usuario=username, senha=password)
        else:
            return render_template("error.html", mensagem= "Usuário já cadastrado")

    
#Valida Loggin
@app.route("/buscador", methods=["GET", "POST"])
def buscador():

    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")

        #valida se usuário existe
        if db.execute("SELECT id FROM users WHERE username = :username", {"username":username}).rowcount == 0:
            return render_template("error.html", mensagem="User Don't Existe, Registrate Please")
        #valida Password e cria uma Session com o ID do usuario
        elif db.execute("SELECT password FROM users WHERE username = :username",{"username": username}).fetchone()[0] == password:
            session["user_id"] = db.execute("SELECT id FROM users WHERE username = :username", {"username": username}).fetchone()[0]
            return render_template("buscador.html")
        else:
            return render_template("error.html", mensagem="User or Password Invalid")
    else:
        return render_template("buscador.html")


#Buscador de Livros
@app.route("/findbooks", methods=["GET", "POST"])
def findbooks():
    #session["book"] = []
    #session["sitereviews"] = []

    if request.method == "POST":
        tipo=request.form.get("tipo")
        search=request.form.get("search")

        if tipo == "1":
            books = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn LIKE :isbn", {"isbn": "%"+search+"%"}).fetchall()
        elif tipo == "2":
            books = db.execute("SELECT isbn, title, author, year FROM books WHERE title LIKE :title", {"title": "%"+search+"%"}).fetchall()
        else:
            books = db.execute("SELECT isbn, title, author, year FROM books WHERE author LIKE :author", {"author": "%"+search+"%"}).fetchall()
        if len(books) == 0:
            return render_template("error.html", mensagem="No match for the search")
        else:
            session['books']=books
            return render_template("lista.html", books=books)
    else:
        return render_template("lista.html", books=session['books'])


#Dados do Livro
@app.route("/bookpage/<string:isbn>")
def bookpage(isbn):

    #busca dados do livro selecionado
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    session["book"] = book
    #busca reviws do livro no site
    sitereviews = db.execute("SELECT review, username FROM reviews WHERE isbn = :isbn",{"isbn": isbn}).fetchall()
    session["sitereviews"] = sitereviews
    #busca rating do livro via API do GoodReads
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "kJNpUr37B9whOGk6igZYA", "isbns": isbn})
    if res.status_code == 404:
        rating = 0
        count_rating = 0
    else:
        data = res.json()
        rating = data["books"][0]["average_rating"]
        count_rating = data["books"][0]["work_ratings_count"]
    session["rating"] = rating
    session["count_rating"] = count_rating

    return render_template("bookpage.html", book=book, sitereviews=sitereviews, rating=rating, count_rating=count_rating)


#Insere Reviews na tabela
@app.route("/addreview", methods=["GET", "POST"])
def addreview():
    if request.method == "POST":
        review = request.form.get("review")
        rating = request.form.get("rating")
        isbn = request.form.get("isbn")
        user_id=session["user_id"]

        #busca usuário que esta fazendo a review
        username = db.execute("SELECT username FROM users WHERE id=:id",{"id":user_id}).fetchone()
        #valida se usuário já tem review para o livro 
        if db.execute("SELECT username FROM reviews WHERE isbn=:isbn AND username=:username",{"isbn":isbn, "username":username[0]}).rowcount == 0:
            #Insere a review na base de dados
            db.execute("INSERT INTO reviews (review, rating, isbn, username) VALUES (:review, :rating, :isbn, :username)",
                        {"review": review, "rating": rating, "isbn": isbn, "username": username[0]})
            db.commit()
            return render_template("reviewadd.html", mensagem="Review was add with SUCESS")
        else:
            return render_template("reviewadd.html", mensagem="You already have one reaview for this book")
    else:
        #Atualzia lista de  reviews do livro no site
        sitereviews = db.execute("SELECT review FROM reviews WHERE isbn = :isbn",{"isbn": session["book"].isbn}).fetchall()
        session["sitereviews"] = sitereviews
        return render_template("bookpage.html", book=session["book"], sitereviews=sitereviews, rating=session["rating"], count_rating=session["count_rating"])


#API busca informações do libro indicado pelo ISBN
@app.route("/api/isbn/<string:isbn>")
def isbn_api(isbn):
    #busca informações do livro
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchone()
    if book is None:
        return jsonify({"Erro, book not found"}),422
    #conta a quantidade de reviews e calcula o rating medio
    review_count = db.execute("SELECT * FROM reviews WHERE isbn=:isbn",{"isbn":isbn}).rowcount
    if review_count == 0:
        average_score = 0
    else:
        total_score = db.execute("SELECT SUM(rating) FROM reviews WHERE isbn=:isbn",{"isbn":isbn}).fetchone()
        average_score = total_score[0]/review_count

    return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": review_count,
            "average_score": average_score
        })