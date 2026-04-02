from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gymtracker-secret-key-2024'

def fmt_date(val, fmt='%b %d, %Y'):
    if not val: return ''
    if hasattr(val, 'strftime'): return val.strftime(fmt)
    for pattern in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
        try:
            from datetime import datetime
            return datetime.strptime(str(val)[:19], pattern[:len(str(val)[:19])]).strftime(fmt)
        except: pass
    return str(val)[:10]

app.jinja_env.filters['fmtdate'] = fmt_date
DATABASE = os.path.join(os.path.dirname(__file__), 'gymtracker.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid

def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT, age INTEGER, weight REAL, height REAL,
            goal TEXT DEFAULT 'strength',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS workout (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duration INTEGER, notes TEXT,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );
        CREATE TABLE IF NOT EXISTS exercise (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'other',
            FOREIGN KEY (workout_id) REFERENCES workout(id)
        );
        CREATE TABLE IF NOT EXISTS exercise_set (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER NOT NULL,
            set_number INTEGER, reps INTEGER, weight REAL, duration INTEGER,
            FOREIGN KEY (exercise_id) REFERENCES exercise(id)
        );
        CREATE TABLE IF NOT EXISTS body_stat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            weight REAL, body_fat REAL, muscle_mass REAL,
            chest REAL, waist REAL, hips REAL, arms REAL, thighs REAL,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );
        CREATE TABLE IF NOT EXISTS personal_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            weight REAL, reps INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );
    ''')
    db.commit(); db.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', username).strip()
        if query('SELECT id FROM user WHERE username=?', (username,), one=True):
            if request.is_json: return jsonify({'error': 'Username taken'}), 400
            flash('Username taken', 'error'); return redirect(url_for('register'))
        if email and query('SELECT id FROM user WHERE email=?', (email,), one=True):
            if request.is_json: return jsonify({'error': 'Email registered'}), 400
            flash('Email registered', 'error'); return redirect(url_for('register'))
        uid = execute('INSERT INTO user (username,email,password_hash,name) VALUES (?,?,?,?)',
                      (username, email, generate_password_hash(password), name))
        session['user_id'] = uid
        if request.is_json: return jsonify({'success': True, 'redirect': url_for('dashboard')})
        return redirect(url_for('dashboard'))
    return render_template('auth.html', mode='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        user = query('SELECT * FROM user WHERE username=?', (data.get('username',''),), one=True)
        if user and check_password_hash(user['password_hash'], data.get('password','')):
            session['user_id'] = user['id']
            if request.is_json: return jsonify({'success': True, 'redirect': url_for('dashboard')})
            return redirect(url_for('dashboard'))
        if request.is_json: return jsonify({'error': 'Invalid credentials'}), 401
        flash('Invalid credentials', 'error')
    return render_template('auth.html', mode='login')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('index'))

def compute_streak(user_id):
    rows = query("SELECT DISTINCT date(date) as d FROM workout WHERE user_id=? ORDER BY d DESC", (user_id,))
    if not rows: return 0
    streak = 0; check = datetime.utcnow().date()
    dates = set(r['d'] for r in rows)
    while check.strftime('%Y-%m-%d') in dates:
        streak += 1; check -= timedelta(days=1)
    return streak

@app.route('/dashboard')
@login_required
def dashboard():
    uid = session['user_id']
    user = query('SELECT * FROM user WHERE id=?', (uid,), one=True)
    now = datetime.utcnow()
    week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
    recent_workouts = query('''
        SELECT w.*, COUNT(e.id) as ex_count FROM workout w
        LEFT JOIN exercise e ON e.workout_id=w.id
        WHERE w.user_id=? GROUP BY w.id ORDER BY w.date DESC LIMIT 5''', (uid,))
    weekly_workouts = query('SELECT COUNT(*) as c FROM workout WHERE user_id=? AND date>=?', (uid, week_start), one=True)['c']
    total_workouts = query('SELECT COUNT(*) as c FROM workout WHERE user_id=?', (uid,), one=True)['c']
    sets = query('''SELECT es.weight, es.reps FROM exercise_set es
        JOIN exercise e ON e.id=es.exercise_id JOIN workout w ON w.id=e.workout_id
        WHERE w.user_id=? AND w.date>=? AND es.weight IS NOT NULL AND es.reps IS NOT NULL''', (uid, week_start))
    weekly_volume = round(sum(s['weight']*s['reps'] for s in sets))
    latest_stat = query('SELECT * FROM body_stat WHERE user_id=? ORDER BY date DESC LIMIT 1', (uid,), one=True)
    prs = query('SELECT * FROM personal_record WHERE user_id=? ORDER BY date DESC LIMIT 5', (uid,))
    streak = compute_streak(uid)
    return render_template('dashboard.html', user=user, recent_workouts=recent_workouts,
        weekly_workouts=weekly_workouts, total_workouts=total_workouts,
        weekly_volume=weekly_volume, latest_stat=latest_stat, prs=prs, streak=streak, now=now)

@app.route('/workouts')
@login_required
def workouts():
    uid = session['user_id']
    page = request.args.get('page', 1, type=int)
    per_page = 10; offset = (page-1)*per_page
    total = query('SELECT COUNT(*) as c FROM workout WHERE user_id=?', (uid,), one=True)['c']
    items = query('''SELECT w.*, COUNT(DISTINCT e.id) as ex_count,
        COALESCE(SUM(CASE WHEN es.weight IS NOT NULL AND es.reps IS NOT NULL THEN es.weight*es.reps ELSE 0 END),0) as volume
        FROM workout w LEFT JOIN exercise e ON e.workout_id=w.id
        LEFT JOIN exercise_set es ON es.exercise_id=e.id
        WHERE w.user_id=? GROUP BY w.id ORDER BY w.date DESC LIMIT ? OFFSET ?''', (uid, per_page, offset))
    pages = max(1, (total+per_page-1)//per_page)
    class Pager:
        def __init__(self):
            self.items=items; self.page=page; self.pages=pages; self.total=total
            self.has_prev=page>1; self.has_next=page<pages
            self.prev_num=page-1; self.next_num=page+1
        def iter_pages(self): return range(1, pages+1)
    return render_template('workouts.html', workouts=Pager())

@app.route('/workout/new', methods=['GET', 'POST'])
@login_required
def new_workout():
    if request.method == 'POST':
        data = request.get_json()
        uid = session['user_id']
        date_str = data.get('date') or datetime.utcnow().strftime('%Y-%m-%d')
        wo_id = execute('INSERT INTO workout (user_id,name,duration,notes,date) VALUES (?,?,?,?,?)',
            (uid, data['name'], data.get('duration'), data.get('notes'), date_str))
        for ex_data in data.get('exercises', []):
            ex_id = execute('INSERT INTO exercise (workout_id,name,category) VALUES (?,?,?)',
                (wo_id, ex_data['name'], ex_data.get('category','other')))
            for i, s in enumerate(ex_data.get('sets', []), 1):
                execute('INSERT INTO exercise_set (exercise_id,set_number,reps,weight) VALUES (?,?,?,?)',
                    (ex_id, i, s.get('reps'), s.get('weight')))
                if s.get('weight') and s.get('reps'):
                    pr = query('SELECT * FROM personal_record WHERE user_id=? AND exercise_name=?',
                        (uid, ex_data['name']), one=True)
                    if not pr or s['weight'] > pr['weight']:
                        if pr: execute('DELETE FROM personal_record WHERE id=?', (pr['id'],))
                        execute('INSERT INTO personal_record (user_id,exercise_name,weight,reps) VALUES (?,?,?,?)',
                            (uid, ex_data['name'], s['weight'], s['reps']))
        return jsonify({'success': True, 'id': wo_id})
    return render_template('new_workout.html')

@app.route('/workout/<int:workout_id>')
@login_required
def view_workout(workout_id):
    uid = session['user_id']
    workout = query('SELECT * FROM workout WHERE id=? AND user_id=?', (workout_id, uid), one=True)
    if not workout: return redirect(url_for('workouts'))
    exercises = query('SELECT * FROM exercise WHERE workout_id=?', (workout_id,))
    ex_list = []
    total_vol = 0; total_sets = 0
    for ex in exercises:
        sets = query('SELECT * FROM exercise_set WHERE exercise_id=? ORDER BY set_number', (ex['id'],))
        vol = sum((s['weight'] or 0)*(s['reps'] or 0) for s in sets if s['weight'] and s['reps'])
        total_vol += vol; total_sets += len(sets)
        ex_list.append({'ex': ex, 'sets': sets, 'vol': int(vol)})
    return render_template('view_workout.html', workout=workout, ex_list=ex_list,
        total_vol=int(total_vol), total_sets=total_sets)

@app.route('/workout/<int:workout_id>/delete', methods=['POST'])
@login_required
def delete_workout(workout_id):
    uid = session['user_id']
    if query('SELECT id FROM workout WHERE id=? AND user_id=?', (workout_id, uid), one=True):
        exs = query('SELECT id FROM exercise WHERE workout_id=?', (workout_id,))
        for ex in exs: execute('DELETE FROM exercise_set WHERE exercise_id=?', (ex['id'],))
        execute('DELETE FROM exercise WHERE workout_id=?', (workout_id,))
        execute('DELETE FROM workout WHERE id=?', (workout_id,))
    return jsonify({'success': True})

@app.route('/progress')
@login_required
def progress():
    uid = session['user_id']
    prs = query('SELECT * FROM personal_record WHERE user_id=? ORDER BY date DESC', (uid,))
    return render_template('progress.html', prs=prs)

@app.route('/api/progress/volume')
@login_required
def api_volume():
    uid = session['user_id']
    days = request.args.get('days', 30, type=int)
    since = (datetime.utcnow()-timedelta(days=days)).strftime('%Y-%m-%d')
    wos = query('SELECT * FROM workout WHERE user_id=? AND date>=? ORDER BY date ASC', (uid, since))
    data = []
    for wo in wos:
        sets = query('''SELECT es.weight,es.reps FROM exercise_set es JOIN exercise e ON e.id=es.exercise_id
            WHERE e.workout_id=? AND es.weight IS NOT NULL AND es.reps IS NOT NULL''', (wo['id'],))
        vol = sum(s['weight']*s['reps'] for s in sets)
        data.append({'date': wo['date'][:10], 'volume': round(vol), 'name': wo['name']})
    return jsonify(data)

@app.route('/api/progress/exercise/<n>')
@login_required
def api_exercise_progress(name):
    uid = session['user_id']
    rows = query('''SELECT w.date, MAX(es.weight) as max_weight, w.name as wname
        FROM exercise_set es JOIN exercise e ON e.id=es.exercise_id JOIN workout w ON w.id=e.workout_id
        WHERE w.user_id=? AND LOWER(e.name) LIKE LOWER(?)
        GROUP BY w.id ORDER BY w.date ASC''', (uid, f'%{name}%'))
    return jsonify([{'date': r['date'][:10], 'max_weight': r['max_weight'], 'workout': r['wname']} for r in rows])

@app.route('/api/progress/bodyweight')
@login_required
def api_bodyweight():
    uid = session['user_id']
    rows = query('SELECT * FROM body_stat WHERE user_id=? ORDER BY date ASC', (uid,))
    return jsonify([{'date': r['date'][:10], 'weight': r['weight'], 'body_fat': r['body_fat']} for r in rows])

@app.route('/api/exercises/names')
@login_required
def api_exercise_names():
    uid = session['user_id']
    rows = query('SELECT DISTINCT e.name FROM exercise e JOIN workout w ON w.id=e.workout_id WHERE w.user_id=?', (uid,))
    return jsonify([r['name'] for r in rows])

@app.route('/api/dashboard/weekly')
@login_required
def api_weekly():
    uid = session['user_id']
    now = datetime.utcnow(); data = []
    for i in range(6, -1, -1):
        day = (now-timedelta(days=i)).strftime('%Y-%m-%d')
        count = query("SELECT COUNT(*) as c FROM workout WHERE user_id=? AND date(date)=?", (uid, day), one=True)['c']
        data.append({'day': (now-timedelta(days=i)).strftime('%a'), 'workouts': count})
    return jsonify(data)

@app.route('/body-stats', methods=['GET', 'POST'])
@login_required
def body_stats():
    uid = session['user_id']
    if request.method == 'POST':
        data = request.get_json()
        date_str = data.get('date') or datetime.utcnow().strftime('%Y-%m-%d')
        execute('''INSERT INTO body_stat (user_id,date,weight,body_fat,muscle_mass,chest,waist,hips,arms,thighs)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (uid, date_str, data.get('weight'), data.get('body_fat'), data.get('muscle_mass'),
             data.get('chest'), data.get('waist'), data.get('hips'), data.get('arms'), data.get('thighs')))
        if data.get('weight'): execute('UPDATE user SET weight=? WHERE id=?', (data['weight'], uid))
        return jsonify({'success': True})
    stats = query('SELECT * FROM body_stat WHERE user_id=? ORDER BY date DESC', (uid,))
    return render_template('body_stats.html', stats=stats)

@app.route('/body-stats/<int:stat_id>/delete', methods=['POST'])
@login_required
def delete_body_stat(stat_id):
    execute('DELETE FROM body_stat WHERE id=? AND user_id=?', (stat_id, session['user_id']))
    return jsonify({'success': True})

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    uid = session['user_id']
    user = query('SELECT * FROM user WHERE id=?', (uid,), one=True)
    if request.method == 'POST':
        data = request.get_json()
        execute('UPDATE user SET name=?,age=?,weight=?,height=?,goal=? WHERE id=?',
            (data.get('name',user['name']), data.get('age'), data.get('weight'),
             data.get('height'), data.get('goal','strength'), uid))
        return jsonify({'success': True})
    return render_template('profile.html', user=user)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
