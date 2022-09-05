# Hi guys! Welcome to my first official project :)
# Backend: Python language + Flask Framework + Boostrap templating language
# Database: SQLite (thanks to SQLAlchemy, a ORM Library, helping me to turn Python Object into SQLite database)
# This is the place for all the python methods lived.


from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

# Let's get started!
app = Flask(__name__)

# To connect with one existed online Movie data source, I need to create one API key.
MOVIE_DB_API_KEY = "878031006c93d37f0fee91ac061d3176"
MOVIE_DB_SEARCH_URL = f'https://api.themoviedb.org/3/search/movie?api_key='
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# this secret key is used for wtforms package
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# I choose to use bootstrap templating package where it has a great CSS style sheets to build beautiful website
Bootstrap(app)

# Create SQLite Database with SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

check = []#check duplicate, because SQLite only accepts unique value

# create table framework
# "nullable=True" means that I allow the input for this variable to be None.
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(300), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

# This is where we could see the data in the SQLite. It is also the default main page of the web
# The rank for all the movies needs to follow ascending order by its movie rating(decided by user)
@app.route("/",methods=["POST","GET"])
def home():
    movies_list = db.session.query(Movie).order_by(Movie.rating).all()     #get the list with order by movie rating
    movies_list = list(movies_list)[::-1]
    print(f"home() -> all movies DB: {movies_list}")    #check whether API works
    for i in range(len(movies_list)): # Give ranking numbers for all movies in the list
        num = i +1
        movies_list[i].ranking = num
    db.session.commit() #revisit the dataset
    return render_template("index.html", movie_list=movies_list)

## First form for adding new movie title to database
class addFindForm(FlaskForm):
    title = StringField("Movie title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

# add new movie to the database
@app.route("/add", methods=["GET", "POST"])
def add():
    print("add")
    add_form = addFindForm()
    if add_form.validate_on_submit():
        movie_title = add_form.title.data
       # if Movie.query.get(movie_title):
            #return render_template("error.html")
        #response = requests.get(f'https://api.themoviedb.org/3/movie/550?api_key={MOVIE_DB_API_KEY}')
        result = requests.get(f'{MOVIE_DB_SEARCH_URL}{MOVIE_DB_API_KEY}&query={movie_title}') #add
        data_info = result.json()['results']
        return render_template("select.html", options=data_info)
    return render_template("add.html", form=add_form)



# This is the form responsible for changing review and rating
class ChangeMovieForm(FlaskForm):
    print("change")
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

# This is the option where people could change their past rating and review
# You could enter either new rating or new review or both!
@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = ChangeMovieForm()
    movie_id = request.args.get("id")
    movie_update = Movie.query.get(movie_id)
    if form.validate_on_submit() and form.submit: #must change the datasource when user submits the change requests
        if form.rating.data: #if user enters new rating, then I changes the rating
            movie_update.rating = float(form.rating.data)
        if form.review.data:  #if user enters new review, then I changes the review
            movie_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie_update, form=form)



# This is the option where people could delete the movie in the dataset
@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie_name = Movie.query.get(movie_id)
    db.session.delete(movie_name)
    db.session.commit()
    check.pop(int(movie_id)-1)
    return redirect(url_for("home"))

@app.route("/clean")
def clean():
    db.session.query(Movie).delete()
    db.session.commit()
    while check:
        check.pop()
    return redirect(url_for("home"))


# Based on user's input and API, I am able to guess what is the name of the movie you are looking at :)
@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")

    if movie_id not in check:
        print("happy",movie_id,check)
        check.append(movie_id)
        movie_url = f"{MOVIE_DB_INFO_URL}/{movie_id}"
        result = requests.get(movie_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = result.json()
        new_Movie = Movie(
            title =data["title"],
                #The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0], #we only want year
            description=data["overview"],
            rating= 0,
            ranking = 10,
            review = "No Review",
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}"

        )
        db.session.add(new_Movie)
        db.session.commit()
        return redirect(url_for('rate_movie', id=new_Movie.id))
    else:
        return render_template("error.html")


if __name__ == '__main__':
    app.run(debug=True)

