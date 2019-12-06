from app import app
from app import login

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy(app)
migrate = Migrate(app, db)

db.Model.metadata.reflect(bind=db.engine, schema='ka7619')

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'trainers': User}

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    __table__ = db.Model.metadata.tables['ka7619.trainers']

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Pokemon(db.Model):
    __table__ = db.Model.metadata.tables['ka7619.pokemon']

    def __str__(self):
        return str({"pok_id": self.pok_id, "pok_name": self.pok_name})

    def __repr__(self):
        return str({"pok_id": self.pok_id, "pok_name": self.pok_name})

    def GetBasicInformation(self):
        return db.session.execute(f"""
            SELECT SELECT p.pok_id as ID, p.pok_name as Name,
	            b.b_hp as HP, b.b_atk as ATK, b.b_def as DEF, b.b_sp_atk as "SP.ATK", b.b_sp_def as "SP.DEF", b.b_speed as SPD
            FROM pokemon p JOIN base_stats b USING(pok_id)
            WHERE p.pok_id = {self.pok_id}
        """).fetchall()

class BaseStats(db.Model):
    __table__ = db.Model.metadata.tables['ka7619.base_stats']

    def __repr__(self):
        return str({"pok_id": self.pok_id, "hp": self.b_hp, "att": self.b_atk, "def": self.b_def})

class PokTypes(db.Model):
    __table__ = db.Model.metadata.tables['ka7619.pokemon_types']

    def __repr__(self):
        return str({"pok_id": self.pok_id, "type_id": self.type_id})

class Types(db.Model):
    __table__ = db.Model.metadata.tables['ka7619.types']

    def __repr__(self):
        return str({"type_id": self.type_id, "type_name": self.type_name})

class Abilities(db.Model):
    __table__ = db.Model.metadata.tables['ka7619.abilities']

    def __repr__(self):
        return str({"ability_id": self.abil_id, "ability_name": self.abil_name})

class PokAbilities(db.Model):
    __table__ = db.Model.metadata.tables['ka7619.pokemon_abilities']

    def __repr__(self):
        return str({"pok_id": self.pok_id, "abil_id": self.abil_id})

class Type_efficacy(db.Model):
    __table__ = db.Model.metadata.tables['ka7619.type_efficacy']

    def __repr__(self):
        return str({"type_damage": self.damage_type_id, "type_target": self.target_type_id, "efficacy": self.damage_factor})

class PokEvolMatch(db.Model):
    __table__ = db.Model.metadata.tables['ka7619.pokemon_evolution_matchup']

    def __repr__(self):
        return str({'pok_id': self.pok_id, 'hab_id': self.hab_id, 'catch_rate': self.capture_rate, 'evolve_from_id': self.evolves_from_species_id})

class Habitats(db.Model):
    __table__ = db.Model.metadata.tables['ka7619.pokemon_habitats']

    def __repr__(self):
        return str({'hab_id': self.hab_id, 'hab_name': self.hab_name})