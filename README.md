# Project 1

Web Programming with Python and JavaScript

This project is from a course from EDX.
This is a web programing using Flask, PostgreeSQL with SQLAlchemy.
Functions:
1-Create account
2-Find book informations by ISBN, Author or title
3-Use an API from GoodBooks to get reviews and aberage rating of a book
4-Let the user make one review about a book

Templates:
layout.html - bring the base of information for the layout to all pages
index.html - login page
formulario.html - form to make an account
cadsucces.html - appears if creating account is succes
error.html - page called when is some error to display a message
buscador.html - page with the form to make a search about a book with ISBN, Title or Author. To find can be use a full information or part of it.
lista.html - Bring the result of teh search with a list of books and some informations
bookpage.html - Bring more information about a book that was chosen in the list.html. Permit the user to make a review about the book
reviewadd.html - Page display if the review was add or if the user already had made review before

application.py:
def index() - Initiation page
def formulario() - Call the create an account page
def cadsucess() - Valid the creation of the account, if is new make one and if is not just display a message
def buscador() - Valid the user and start a session. Call the page to serach a book
def findbooks() - Make the search of a book using ISBN, Author or title
def bookpage(isbn) - Bring the page with more information about a book, need to be passed the information ISBN. Bring all the review about the book tha was made on the site
def addreview() - Check if exist a review about the book from the user, if is not add the review and update the list of reviews on the page

API to get informations of a book from the site, need to pass a valid ISBN
@app.route("/api/isbn/<string:isbn>")
def isbn_api(isbn):

({
    "title": book.title,
    "author": book.author,
    "year": book.year,
    "isbn": book.isbn,
    "review_count": review_count,
    "average_score": average_score
})





