import sqlite3
import hashlib
import random
from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, flash, g
)
from functools import wraps

# --- Konfigurasi Aplikasi ---
app = Flask(__name__)
# Kunci rahasia diperlukan untuk 'session' dan 'flash'
app.secret_key = "kunci_rahasia_kuis_anda_yang_sangat_aman" 
DB_NAME = "soal.db"

# --- Fungsi Hashing (dari main.py) ---
def hash_password(password):
    """Fungsi hashing sederhana untuk simulasi keamanan."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- Fungsi Bantuan Database ---
def get_db():
    """Membuka koneksi database per-request."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row  # Ini penting agar bisa akses kolom via nama
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Menutup koneksi database di akhir request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Decorator untuk Autentikasi ---
def login_required(f):
    """Decorator untuk memastikan user sudah login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Anda harus login untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator untuk memastikan user adalah admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Anda harus login untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Hanya admin yang bisa mengakses halaman ini.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rute Autentikasi (Login/Register/Logout) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, hashed_password)
        ).fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'Selamat datang, {user["username"]}!', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Username atau password salah.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username dan password tidak boleh kosong.', 'warning')
            return render_template('register.html')
            
        hashed_password = hash_password(password)
        db = get_db()
        
        try:
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, hashed_password, 'user')
            )
            db.commit()
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username sudah digunakan.', 'danger')
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('login'))

# --- Rute Panel Admin ---

@app.route('/admin')
@admin_required
def admin():
    db = get_db()
    semua_soal = db.execute("SELECT * FROM soal ORDER BY bahasa, id").fetchall()
    return render_template('admin.html', semua_soal=semua_soal)

@app.route('/admin/tambah', methods=['POST'])
@admin_required
def tambah_soal():
    pertanyaan = request.form['pertanyaan']
    pilihan = request.form['pilihan'] # "A,B,C,D"
    jawaban = request.form['jawaban']
    bahasa = request.form['bahasa']
    
    db = get_db()
    db.execute(
        "INSERT INTO soal (pertanyaan, pilihan, jawaban, bahasa) VALUES (?, ?, ?, ?)",
        (pertanyaan, pilihan, jawaban, bahasa)
    )
    db.commit()
    flash('Soal baru berhasil ditambahkan.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/hapus', methods=['POST'])
@admin_required
def hapus_soal():
    soal_id = request.form['soal_id']
    db = get_db()
    db.execute("DELETE FROM soal WHERE id = ?", (soal_id,))
    db.commit()
    flash('Soal berhasil dihapus.', 'success')
    return redirect(url_for('admin'))

# --- Rute Kuis Utama ---

@app.route('/')
@login_required
def index():
    """Halaman utama untuk memilih bahasa kuis."""
    return render_template('index.html')

@app.route('/kuis/mulai/<string:bahasa>')
@login_required
def mulai_kuis(bahasa):
    """Mempersiapkan sesi kuis baru."""
    db = get_db()
    soal_rows = db.execute("SELECT * FROM soal WHERE bahasa = ?", (bahasa,)).fetchall()
    
    # Ubah sqlite3.Row menjadi dict agar bisa disimpan di session
    semua_soal = [dict(row) for row in soal_rows]
    random.shuffle(semua_soal)
    
    session['semua_soal'] = semua_soal
    session['index'] = 0
    session['skor'] = 0
    
    if not semua_soal:
        flash(f'Maaf, belum ada soal untuk bahasa {bahasa}.', 'warning')
        return redirect(url_for('index'))
        
    return redirect(url_for('kuis'))

@app.route('/kuis', methods=['GET', 'POST'])
@login_required
def kuis():
    """Menangani tampilan soal dan jawaban."""
    if 'semua_soal' not in session or not session['semua_soal']:
        flash('Silakan pilih bahasa untuk memulai kuis.', 'info')
        return redirect(url_for('index'))

    index = session.get('index', 0)
    semua_soal = session.get('semua_soal', [])

    # Jika kuis sudah selesai
    if index >= len(semua_soal):
        return redirect(url_for('hasil'))

    # Logika jika user MENJAWAB soal (POST)
    if request.method == 'POST':
        jawaban_user = request.form.get('jawaban_user')
        soal_benar = semua_soal[index]['jawaban']
        
        if jawaban_user == soal_benar:
            session['skor'] = session.get('skor', 0) + 1
            flash('Jawaban Anda Benar!', 'success')
        else:
            flash(f'Jawaban Anda Salah. Jawaban yang benar: {soal_benar}', 'danger')
            
        session['index'] = index + 1
        
        # Cek lagi apa sudah selesai setelah increment
        if session['index'] >= len(semua_soal):
            return redirect(url_for('hasil'))
        else:
            return redirect(url_for('kuis')) # Pindah ke soal berikutnya

    # Logika jika user MELIHAT soal (GET)
    soal_sekarang = semua_soal[index]
    pilihan_list = soal_sekarang['pilihan'].split(',')
    
    return render_template(
        'kuis.html',
        soal=soal_sekarang,
        pilihan_list=pilihan_list,
        nomor_soal=index + 1,
        total_soal=len(semua_soal)
    )

@app.route('/hasil')
@login_required
def hasil():
    """Menampilkan skor akhir."""
    skor = session.get('skor', 0)
    total_soal = len(session.get('semua_soal', []))
    
    # Hapus data kuis dari session
    session.pop('semua_soal', None)
    session.pop('index', None)
    session.pop('skor', None)
    
    return render_template('hasil.html', skor=skor, total_soal=total_soal)

print("="*40)
print(f"DEBUG: Script app.py sedang dibaca...")
print(f"DEBUG: Nilai __name__ saat ini adalah: {__name__}")
print("="*40)

# --- Menjalankan Aplikasi ---
if __name__ == '__main__':
    print(">>> SERVER: Kondisi __main__ terpenuhi. Mencoba menjalankan server...")
    app.run(debug=True) # debug=True untuk mode pengembangan
else:
    print(">>> SERVER: Kondisi __main__ TIDAK terpenuhi. Server tidak akan jalan.")