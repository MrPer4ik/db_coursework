from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from flask_paginate import Pagination
from werkzeug.urls import url_parse


from app import app
from app.forms import LoginForm, RegistrationForm, EditingQuery, AddBuddy
from app.models import Pokemon, User, BaseStats, PokTypes, Types, \
    Abilities, PokAbilities, Type_efficacy, PokEvolMatch, Habitats, db

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
@login_required
def index():
    fav_pokemon = User.query.join(Pokemon, Pokemon.pok_id == User.pok_id)\
        .add_columns(Pokemon.pok_name, Pokemon.pok_id).filter(User.id == current_user.id).first()
    return render_template('index.html', fav_pokemon=fav_pokemon, title="Home")

@app.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    return render_template('support.html', title="Support")

@app.route('/database',  strict_slashes=False, methods=['GET', 'POST'])
@login_required
def database():
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', '', type=str)
    filt = request.args.get('filt_by', '', type=str)
    search = request.args.get('search', type=str)

    res = Pokemon.query.join(BaseStats, Pokemon.pok_id==BaseStats.pok_id)\
        .add_columns(Pokemon.pok_id, Pokemon.pok_name, BaseStats.b_hp, BaseStats.b_atk,\
        BaseStats.b_def, BaseStats.b_sp_atk, BaseStats.b_sp_def, BaseStats.b_speed)

    # form = request.form if request.method == "POST" else EditingQuery()
    form = EditingQuery()

    if filt is None and form.filterField.data is None:
        filt = 'desc'

    sort = form.sortedField.data if len(sort)==0 else sort
    filt = form.filterField.data if filt is None else filt
    search = form.searchField.data if search is None else search

    if request.method == "POST":
        if form.sortedField.data != sort or form.searchField.data != search or form.filterField.data != filt:
            page = 1
        res = res.order_by(form.sortedField.data + (f' {form.filterField.data}' if form.filterField.data is not None else ''))
        if form.searchField.data is not None:
            res = res.filter(Pokemon.pok_name.startswith(form.searchField.data))
    else:        
        res = res.order_by(sort + (f' {filt}' if filt is not None else ''))
        if search is not None:
            res = res.filter(Pokemon.pok_name.startswith(search))


    pagination = Pagination(page=page,  sort=form.sortedField.data, filt_by=form.filterField.data, search=form.searchField.data,\
         per_page=app.config['CARDS_PER_PAGE'], css_framework='foundation', total=res.count())

    res = res.paginate(page, app.config['CARDS_PER_PAGE'], False)

    types = Pokemon.query.join(PokTypes, Pokemon.pok_id==PokTypes.pok_id).\
        join(Types, PokTypes.type_id==Types.type_id).add_columns(Pokemon.pok_id, Types.type_name)

    form.sortedField.data = form.sortedField.data if request.method=="POST" else sort
    form.filterField.data = form.filterField.data if request.method=="POST" else filt
    form.searchField.data = form.searchField.data if request.method=="POST" else search
    next_url = url_for('database', page=res.next_num, sort=form.sortedField.data, filt_by=form.filterField.data, search=form.searchField.data) if res.has_next else None
    prev_url = url_for('database', page=res.prev_num, sort=form.sortedField.data, filt_by=form.filterField.data, search=form.searchField.data) if res.has_prev else None

    return render_template('database.html', data=res.items, next_url=next_url, prev_url=prev_url, types=types.all(), form=form, pagination=pagination, title="Database")


@app.route('/pokemon/<pok_id>', methods=['GET', 'POST'])
@login_required
def pokemon(pok_id):
    fav_pokemon = User.query.filter(User.id == current_user.id).first()

    form = AddBuddy()
    if form.validate_on_submit():
        fav_pokemon.pok_id = pok_id
        db.session.commit()
        return redirect(url_for('index'))

    res = Pokemon.query.join(BaseStats, Pokemon.pok_id==BaseStats.pok_id).filter(Pokemon.pok_id == pok_id)\
        .add_columns(Pokemon.pok_id, Pokemon.pok_name, Pokemon.pok_height, Pokemon.pok_weight, BaseStats.b_hp, BaseStats.b_atk,\
        BaseStats.b_def, BaseStats.b_sp_atk, BaseStats.b_sp_def, BaseStats.b_speed).first()

    types = Types.query.join(PokTypes, PokTypes.type_id==Types.type_id).join(Pokemon, Pokemon.pok_id==PokTypes.pok_id)\
        .add_columns(Types.type_name).filter(Pokemon.pok_id==pok_id).all()

    effect = db.engine.execute(f'''
        SELECT DISTINCT typ.type_name as EFF, eff.damage_factor as DAMAGE
        FROM pokemon_types t JOIN type_efficacy eff ON (t.type_id = eff.damage_type_id)
	        JOIN types typ ON (eff.target_type_id = typ.type_id)
        WHERE t.pok_id = {pok_id} and t.slot = 1
    ''').fetchall()

    abilities = Abilities.query.join(PokAbilities, PokAbilities.abil_id==Abilities.abil_id).join(Pokemon, Pokemon.pok_id==PokAbilities.pok_id)\
        .add_columns(Abilities.abil_name, PokAbilities.is_hidden).filter(Pokemon.pok_id==pok_id).all()

    habitat_cap_rate = PokEvolMatch.query.join(Habitats, PokEvolMatch.hab_id==Habitats.hab_id).add_columns(Habitats.hab_name, Habitats.hab_descript)\
        .filter(PokEvolMatch.pok_id==pok_id).all()

    evolves_from = PokEvolMatch.query.join(Pokemon, Pokemon.pok_id==PokEvolMatch.pok_id).filter(PokEvolMatch.pok_id==pok_id).all()

    evolves_from_from = db.engine.execute(f'''
        SELECT b.evolves_from_species_id as PreEvol
        FROM pokemon_evolution_matchup a JOIN pokemon_evolution_matchup b
	        ON (a.evolves_from_species_id = b.pok_id)
        WHERE a.pok_id = {pok_id}
    ''').fetchall()

    evolves_to = PokEvolMatch.query.filter(PokEvolMatch.evolves_from_species_id==pok_id).all()

    evolves_to_to = db.engine.execute(f'''
        SELECT b.pok_id as Post_evol
        FROM pokemon_evolution_matchup a JOIN pokemon_evolution_matchup b
	        ON (a.pok_id = b.evolves_from_species_id)
        WHERE a.evolves_from_species_id = {pok_id}
    ''').fetchall()

    return render_template('pok_details.html', data=res, types=types, abilities=abilities, effect=effect, habitat_cap_rate=habitat_cap_rate,\
        evolves_from=evolves_from, evolves_from_from=evolves_from_from, evolves_to=evolves_to, evolves_to_to=evolves_to_to, form=form, fav_pokemon=fav_pokemon, title=res.pok_name.capitalize())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
