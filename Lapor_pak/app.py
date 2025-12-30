from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jombang-beriman-123'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
# Database URI - Sesuaikan jika menggunakan password di MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/lapor_pak'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# --- MODEL DATABASE ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Panjang 255 untuk menyimpan Hash


class Laporan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(200))
    kategori = db.Column(db.String(100))
    deskripsi = db.Column(db.Text)
    foto = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Menunggu')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- ROUTES MASYARAKAT ---
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    judul = request.form.get('judul')
    kategori = request.form.get('kategori')
    deskripsi = request.form.get('deskripsi')
    foto = request.files['foto']

    if foto:
        foto_name = foto.filename
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_name))
        baru = Laporan(judul=judul, kategori=kategori, deskripsi=deskripsi, foto=foto_name)
        db.session.add(baru)
        db.session.commit()
    return render_template('index.html', sukses=True)


# --- ROUTES ADMIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        # Menggunakan check_password_hash untuk verifikasi keamanan
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Username atau Password salah!')
    return render_template('login.html')


@app.route('/admin')
@login_required
def admin_dashboard():
    laporan_list = Laporan.query.order_by(Laporan.id.desc()).all()

    # Hitung data statistik untuk Chart.js (Donut Chart)
    stats = db.session.query(Laporan.kategori, func.count(Laporan.id)).group_by(Laporan.kategori).all()
    labels = [s[0] for s in stats]
    values = [s[1] for s in stats]

    return render_template('admin.html', laporan=laporan_list, labels=labels, values=values)


@app.route('/update_status/<int:id>/<string:status_baru>')
@login_required
def update_status(id, status_baru):
    lap = Laporan.query.get(id)
    if lap:
        lap.status = status_baru
        db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- INISIALISASI ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Buat user admin otomatis dengan Password Hashing jika belum ada
        if not User.query.filter_by(username='admin').first():
            hashed_pw = generate_password_hash('password123')
            db.session.add(User(username='admin', password=hashed_pw))
            db.session.commit()

    # Menjalankan aplikasi (Siap untuk Lokal maupun VPS)
    app.run(host='0.0.0.0', port=5000, debug=True)