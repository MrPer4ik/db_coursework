from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse


from app import app
from app.forms import LoginForm, RegistrationForm, EditingQuery
from app.models import Pokemon, User, BaseStats, PokTypes, Types, Abilities, PokAbilities, Type_efficacy, db

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
@login_required
def index():
    return render_template('index.html')

@app.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    return render_template('support.html')

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
    
    res = res.paginate(page, app.config['CARDS_PER_PAGE'], False)

    types = Pokemon.query.join(PokTypes, Pokemon.pok_id==PokTypes.pok_id).\
        join(Types, PokTypes.type_id==Types.type_id).add_columns(Pokemon.pok_id, Types.type_name)

    form.sortedField.data = form.sortedField.data if request.method=="POST" else sort
    form.filterField.data = form.filterField.data if request.method=="POST" else filt
    form.searchField.data = form.searchField.data if request.method=="POST" else search
    next_url = url_for('database', page=res.next_num, sort=form.sortedField.data, filt_by=form.filterField.data, search=form.searchField.data) if res.has_next else None
    prev_url = url_for('database', page=res.prev_num, sort=form.sortedField.data, filt_by=form.filterField.data, search=form.searchField.data) if res.has_prev else None
    
    return render_template('database.html', data=res.items, next_url=next_url, prev_url=prev_url, types=types.all(), form=form)

'''
    #pokemon
    name
    height
    weight
    types
    stats * 6
    abilities (basic, hidden)
    weak to
    immune to
    resistant to
    habitat
    catch rate
    evolutions **
'''
@app.route('/pokemon/<pok_id>')
@login_required
def pokemon(pok_id):
    res = Pokemon.query.join(BaseStats, Pokemon.pok_id==BaseStats.pok_id).filter(Pokemon.pok_id == pok_id)\
        .add_columns(Pokemon.pok_id, Pokemon.pok_name, Pokemon.pok_height, Pokemon.pok_weight, BaseStats.b_hp, BaseStats.b_atk,\
        BaseStats.b_def, BaseStats.b_sp_atk, BaseStats.b_sp_def, BaseStats.b_speed)

    types = Types.query.join(PokTypes, PokTypes.type_id==Types.type_id).join(Pokemon, Pokemon.pok_id==PokTypes.pok_id)\
        .add_columns(Types.type_name).filter(Pokemon.pok_id==pok_id).all()
        
    not_eff = db.session.execute(f'''
        SELECT DISTINCT typ.type_name as NOT_EFF, eff.damage_factor as DAMAGE
        FROM pokemon_types t JOIN type_efficacy eff ON (t.pok_id = eff.damage_type_id)
	    JOIN types typ ON (eff.target_type_id = typ.type_id)
        WHERE t.pok_id = {pok_id} and eff.damage_factor < 100
    ''').fetchall()

    eff = db.session.execute(f'''
        SELECT DISTINCT typ.type_name as NOT_EFF, eff.damage_factor as DAMAGE
        FROM pokemon_types t JOIN type_efficacy eff ON (t.pok_id = eff.damage_type_id)
	    JOIN types typ ON (eff.target_type_id = typ.type_id)
        WHERE t.pok_id = {pok_id} and eff.damage_factor = 100
    ''').fetchall()

    sup_eff = db.session.execute(f'''
        SELECT DISTINCT typ.type_name as NOT_EFF, eff.damage_factor as DAMAGE
        FROM pokemon_types t JOIN type_efficacy eff ON (t.pok_id = eff.damage_type_id)
	    JOIN types typ ON (eff.target_type_id = typ.type_id)
        WHERE t.pok_id = {pok_id} and eff.damage_factor > 100
    ''').fetchall()

    #types.join(Type_efficacy, Type_efficacy.damage_type_id==Types.type_id)\
    #    .join(Types, Types.type_id==Type_efficacy.target_type_id).add_columns(Type_efficacy.target_type_id).filter(Pokemon.pok_name==pok_name).all()

    abilities = Abilities.query.join(PokAbilities, PokAbilities.abil_id==Abilities.abil_id).join(Pokemon, Pokemon.pok_id==PokAbilities.pok_id)\
        .add_columns(Abilities.abil_name, PokAbilities.is_hidden).filter(Pokemon.pok_id==pok_id).all()

    return render_template('pok_details.html', data=res.all(), types=types, abilities=abilities, not_eff=not_eff, eff=eff, sup_eff=sup_eff)

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
