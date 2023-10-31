from flask import Flask, request, render_template
#from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
import mysql.connector
from sqlalchemy import text
import requests


apiURL = "https://pokeapi.co/api/v2/pokemon/"
itemURL = "https://pokeapi.co/api/v2/item/"
#I have put a limit so it only shows the first 20 items in the api
itemsURL ="https://pokeapi.co/api/v2/item/?limit=20"

app = Flask(__name__)

#Connection to my custom pokeAPI database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Tim10ses@127.0.0.1:3306/PokeApi'
db = SQLAlchemy(app)

class Pokemon(db.Model):
    __tablename__ = 'pokemon'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    type = db.Column(db.String(255), nullable=False)

    def __init__(self, name, type):
        self.name = name
        self.type = type

#--------------------------------------


@app.route('/')
def index():
    return render_template('index.html')


#---------------------------------------
#Recieve the data from the search site for the pokemons name
@app.route('/search', methods=['POST','GET'])

def search():
    success_message = None
    error_message = None
    pokemon_name = ""
    if request.method == 'POST':
        if 'findPokemon' in request.form:
            pokemonName = request.form["pokemonName"].lower()
            print("Finding Pokemon:")
            realURL = apiURL+pokemonName+"/"
            response = requests.get(realURL)
            if response.status_code == 200:
                pokemon_data = response.json()
            
            
                pokemon_name = pokemon_data['name']
                types = [entry['type']['name'] for entry in pokemon_data['types']]
                pokemon_sprite_url = pokemon_data['sprites']['front_default']
            
                return render_template('search.html', pokemon_name = pokemon_name, pokemon_type = types, pokemon_sprite_url = pokemon_sprite_url)
            else:
                print("Couldnt find pokemon in the API")
                
                #The function to check the mySQL
                try:
                    print('Trying the mySQL for the pokemon: '+pokemonName)
                     # Query the MySQL database for the Pokemon's name
                    db_pokemon = Pokemon.query.filter_by(name=pokemonName).one()
                    print(db_pokemon)
                    if db_pokemon:
                        print("Found pokemon")
                        pokemon_sprite_url = "static/questionMark.png"
                        pokemon_name = db_pokemon.name
                        types = db_pokemon.type
                        print("Pokemon name: "+pokemon_name+" and its typing is: "+types)
                        return render_template('search.html', pokemon_name = pokemon_name, pokemon_type = types, pokemon_sprite_url=pokemon_sprite_url)
                    else:
                        print("Cant find the pokemon in the MySQL")
                        return render_template ('search.html')
                    
                except NoResultFound:
                    print("Error happened when looking for Database pokemon")
                    return render_template('search.html', error_message=error_message)
            
        #Create the pokemon
        elif 'createPokemon' in request.form:
            print("Creating pokemon")
            new_pokemon_name = request.form['pokemon_name']
            new_pokemon_type = request.form['pokemon_type']
            try:
                realURL = apiURL + new_pokemon_name + "/"
                print(realURL)
                response = requests.get(realURL)
                if response.status_code == 200:
                    print("The pokemon already exists")
                    return render_template('search.html')
                else:
                    print("The pokemon doesn't exist")
                    if new_pokemon_name.isalpha():
                        insert_query = text("INSERT INTO pokemon (name, type) VALUES (:name, :type)")
                        db.session.execute(insert_query, {'name': new_pokemon_name, 'type': new_pokemon_type})
                        db.session.commit()
                        success_message = "Pokemon added successfully!"
                    else:    
                        error_message = "The pokemon typed isnt only letters or is null"   
                    return render_template('search.html', error_message=error_message)
            except Exception as e:
                db.session.rollback()
                #Makes it easier to find out what the bug is >:(
                error_message = f"An error occurred: {str(e)}"
        
            return render_template('search.html', success_message=success_message, error_message=error_message)
    return render_template('search.html')


#-----------------------------------------------------------------------------
#This is the pokemart and just acts as a showcase of the first 20 items in the pokemon item list
@app.route('/pokemart')
def items():
    
    response = requests.get(itemURL)
    data = response.json()
    items = data['results']
    item_info_list = []
    
    #Forloop to check for the 20 items in the api
    for item in items:
            item_id = item['url'].split('/')[-2]
            item_url = f"https://pokeapi.co/api/v2/item/{item_id}/"
            item_response = requests.get(item_url)
            item_data = item_response.json()

            item_name = item_data['name']
            item_effect = item_data['effect_entries'][0]['effect']

            item_info_list.append({'name': item_name, 'effect': item_effect})

    return render_template('pokemart.html', items=item_info_list)
        


#----------------------------------------------------------F-------------------
#This part can change the pokemons name and typing, and it can delete pokemon that exist on the database
#MISSING = Blacklisting on the API
@app.route('/change', methods=['POST','GET'])
def change():
    if 'changePokemon' in request.form:
        success_message = None
        error_message = None
        if request.method == 'POST':
            if 'changePokemon' in request.form:
                pokemon_name = request.form["pokemon_name"].lower()
                pokemon_newName = request.form["pokemon_newName"].lower()
                
                pokemon_newType = request.form["pokemon_newType"].lower()

                try:
                    update_query = text("UPDATE pokemon SET name = :new_name, type = :new_type WHERE name = :original_name")
                    db.session.execute(update_query, {'new_name': pokemon_newName, 'new_type': pokemon_newType, 'original_name': pokemon_name})
            
                    db.session.commit()

                    success_message = "Pokemon name changed successfully!"
                except Exception as e:
                    db.session.rollback()
                    error_message = f"An error occurred: {str(e)}"

                return render_template('change.html', success_message=success_message, error_message=error_message)
            else:
                return render_template('change.html')
        return render_template('change.html')
    
    
    
    elif 'deletePokemon' in request.form:
        print('Deleting Pokemon')
        if request.method == 'POST':
            pokemon_name = request.form.get("pokemon_name").lower()
            
            # Check if the Pokémon exists in the database
            pokemon = Pokemon.query.filter_by(name=pokemon_name).first()
            if pokemon:
                db.session.delete(pokemon)
                db.session.commit()
                return render_template('change.html')
                print('Successfull Delete')
            else:
                #Here it has to blacklist it from the api
        
                return render_template('change.html')
        else:
            return render_template('change.html')
    else:
        return render_template('change.html')





