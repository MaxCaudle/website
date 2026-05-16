import os
import json
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tables import tables, Food, Recipe, Review


class Database:
    """ A class to handle all interactions with a Database. It takes an optional config_file location,
        in case you want to save your config elsewhere."""

    def __init__(self, config_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')):
        self.config_file = config_file

        self.grab_data()
        self.get_session()

        self.con = None

    def grab_data(self):
        """ Grabs the data from the config file and also makes a DATABSE_URI. I believe psycopg2 convention is
            to have that variable name in all caps."""
        with open(self.config_file, 'r') as infile:
            self.data = json.load(infile)

        self.host = os.environ.get('DB_HOST', self.data.get('host', 'localhost'))
        self.port = int(os.environ.get('DB_PORT', self.data.get('port', 5432)))
        self.user = os.environ.get('DB_USER', self.data.get('database_user', 'postgres'))
        self.password = os.environ.get('DB_PASSWORD', self.data.get('database_password', ''))
        self.dbname = os.environ.get('DB_NAME', self.data.get('server_name', 'baking'))

        # Scheme: "postgres+psycopg2://<USERNAME>:<PASSWORD>@<IP_ADDRESS>:<PORT>/<DATABASE_NAME>"
        self.DATABASE_URI = (
            f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        )

    def get_session(self):
        """ This safely makes a sqlalchemy connection engine and a Session instance. The Session isn't fully formed,
            so we can keep making new ones off the same instance."""
        self.engine = create_engine(self.DATABASE_URI)
        self.Session = sessionmaker(bind=self.engine)

    def create_database(self, dbname):
        """ This will make a new database, to help with setup."""

        con = psycopg2.connect(user=self.user,
                               host=self.host or None,
                               password=self.password,
                               port=self.port)
        con.autocommit = True
        cur = con.cursor()

        try:
            cur.execute(f"""CREATE DATABASE {dbname}
                            WITH 
                            OWNER = {self.data['database_user']}
                            ENCODING = 'UTF8'
                            CONNECTION LIMIT = -1;"""
                        )
            print(f"Made {dbname} database")
        except psycopg2.errors.DuplicateDatabase:
            print('Duplicate Database, passing')

    def create_tables(self, dbname, tables):
        """ This safely makes the DB's only table, called weather_app. It takes an optional name parameter, in case we
            want to further customize the emails later."""

        con = psycopg2.connect(dbname=dbname,
                               user=self.user,
                               host=self.host or None,
                               password=self.password,
                               port=self.port)
        con.autocommit = True
        cur = con.cursor()

        for table in tables:
            try:
                create = f"CREATE TABLE {table['name']} (" +\
                         f"{', '.join(table['columns'])});"

                cur.execute(create)
                print(f"Made {table['name']} table")

            except psycopg2.errors.DuplicateTable:
                print('Duplicate Table, passing')

    def add_food(self, name):
        """ Adds an email to the data base."""

        session = self.Session()
        food = Food(name=name)
        print(self.data['database_password'])
        session.add(food)
        session.commit()

        session.refresh(food)
        session.close()

        return int(food.id)

    def delete_food(self, id):
        session = self.Session()
        query = session.query(Food).filter(Food.id == id)
        query.delete()
        session.commit()

    def add_recipe(self, food_id, recipe_name, directions, change, notes, ingredients):
        session = self.Session()
        recipe = Recipe(food_id=food_id,
                        recipe_name=recipe_name,
                        directions=directions,
                        change=change,
                        notes=notes,
                        ingredients=ingredients)
        session.add(recipe)
        session.commit()

        session.refresh(recipe)

        session.close()

        return int(recipe.recipe_id)

    def delete_recipe(self, recipe_id):
        session = self.Session()
        query = session.query(Recipe).filter(Recipe.recipe_id == recipe_id)
        query.delete()
        session.commit()

    def add_review(self, recipe_id, reviewer_name, taste, texture, appearance, overall, comments):
        session = self.Session()
        review = Review(recipe_id=recipe_id,
                        reviewer_name=reviewer_name,
                        taste=taste,
                        texture=texture,
                        appearance=appearance,
                        overall=overall,
                        comments=comments)

        session.add(review)
        session.commit()
        session.close()

    def delete_review(self, review_id):
        session = self.Session()
        query = session.query(Review).filter(Review.review_id == review_id)
        query.delete()
        session.commit()

    def query_foods(self):
        self.make_query_con()

        cur = self.con.cursor()
        cur.execute("""SELECT id, name FROM food;""")
        foods = {food[1]: food[0] for food in cur.fetchall()}

        return foods

    def query_recipes(self, food_id):
        self.make_query_con()

        cur = self.con.cursor()
        cur.execute(f"""SELECT recipe_name, change, recipe_id FROM recipe
                        WHERE food_id = {food_id}
                        ORDER BY recipe_id; """)

        recipes = cur.fetchall()
        recipes = {recipe[2]: (recipe[0], recipe[1]) for recipe in recipes}

        return recipes

    def query_reviews(self, recipe_id):
        self.make_query_con()
        cur = self.con.cursor()
        cur.execute(f"""SELECT * from recipe
                        WHERE recipe_id = {recipe_id}; """)

        recipe = cur.fetchall()

        cur.execute(f"""SELECT * from reviews
                                WHERE recipe_id = {recipe_id}; """)

        reviews = cur.fetchall()
        return recipe, reviews

    def make_query_con(self):
        if not self.con:
            self.con = psycopg2.connect(dbname=self.dbname,
                                        user=self.user,
                                        host=self.host or None,
                                        port=self.port,
                                        password=self.password)

    def food_name_from_id(self, food_id):
        self.make_query_con()
        cur = self.con.cursor()
        cur.execute(f"""SELECT food from food
                                WHERE id = '{food_id}'; """)

        foods = cur.fetchall()
        food = foods[0][0].split(",")[1][1:-2]

        return food



if __name__ == "__main__":
    database = Database()
    database.create_database(dbname='baking')

    database.create_tables(dbname='baking', tables=tables)

