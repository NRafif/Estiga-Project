from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from flask_caching import Cache
from sqlalchemy import text
import io
import pandas as pd
from werkzeug.utils import secure_filename

# Konfigurasi logging - ubah level ke ERROR untuk produksi
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://root:@localhost/estimasi_gadai')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Tambahkan konfigurasi untuk mengoptimalkan database
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30

# Inisialisasi cache
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

db = SQLAlchemy(app)

# Model untuk User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    def __repr__(self):
        return f'<User {self.username}>'

# Model untuk data gadai
class Gadai(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_pemohon = db.Column(db.String(100), nullable=False)
    merk_hp = db.Column(db.String(50), nullable=False)
    tipe_hp = db.Column(db.String(50), nullable=False)
    ram = db.Column(db.Integer, nullable=False)  # dalam GB
    penyimpanan = db.Column(db.Integer, nullable=False)  # dalam GB
    tahun_keluaran = db.Column(db.Integer, nullable=False)
    harga_beli = db.Column(db.Float, nullable=False)
    kondisi = db.Column(db.String(50), nullable=False)  # seperti "90%", "80%", dll
    tanggal_gadai = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    estimasi_pinjaman = db.Column(db.Float, nullable=False)
    estimasi_minimum = db.Column(db.Float, nullable=True)  # untuk rentang estimasi
    estimasi_maximum = db.Column(db.Float, nullable=True)  # untuk rentang estimasi
    is_from_history = db.Column(db.Boolean, default=True)  # menandai apakah estimasi dari data historis
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Kolom untuk verifikasi
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, verified, rejected
    nilai_setelah_verifikasi = db.Column(db.Float, nullable=True)
    catatan_verifikasi = db.Column(db.Text, nullable=True)
    tanggal_verifikasi = db.Column(db.DateTime, nullable=True)
    verifikator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

# Model untuk data historis HP
class DataHistorisHP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merk_hp = db.Column(db.String(50), nullable=False)
    tipe_hp = db.Column(db.String(50), nullable=False)
    ram = db.Column(db.Integer, nullable=False)  # dalam GB
    penyimpanan = db.Column(db.Integer, nullable=False)  # dalam GB
    tahun_keluaran = db.Column(db.Integer, nullable=False)
    nilai_gadai = db.Column(db.Float, nullable=False)
    tanggal_transaksi = db.Column(db.DateTime, nullable=False)

# Model untuk estimasi
class Estimasi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_pemohon = db.Column(db.String(100), nullable=False)
    merk_hp = db.Column(db.String(50), nullable=False)
    tipe_hp = db.Column(db.String(50), nullable=False)
    ram = db.Column(db.Integer, nullable=False)
    penyimpanan = db.Column(db.Integer, nullable=False)
    tahun_keluaran = db.Column(db.Integer, nullable=False)
    harga_beli = db.Column(db.Float, nullable=False)
    kondisi = db.Column(db.String(10), nullable=False)
    estimasi_pinjaman = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Menunggu Persetujuan')  # Menunggu Persetujuan/Disetujui/Ditolak
    tanggal_pengajuan = db.Column(db.DateTime, default=datetime.utcnow)
    tanggal_persetujuan = db.Column(db.DateTime)
    catatan_admin = db.Column(db.Text)

# Model untuk data barang referensi
class DataBarangReferensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merk = db.Column(db.String(100), nullable=False)
    tipe = db.Column(db.String(100), nullable=False)
    ram = db.Column(db.Integer, nullable=False)
    penyimpanan = db.Column(db.Integer, nullable=False)
    tahun_rilis = db.Column(db.Integer, nullable=False)
    harga_pasar = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

# Login required decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Admin required decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Anda tidak memiliki akses ke halaman ini', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        logger.debug(f"Mencoba login dengan username: {username}")
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            logger.debug(f"User ditemukan: {user}")
            logger.debug(f"Password hash tersimpan: {user.password}")
            
            # Coba verifikasi password
            is_valid = check_password_hash(user.password, password)
            logger.debug(f"Hasil verifikasi password: {is_valid}")
            
            if is_valid:
                logger.debug("Password cocok, login berhasil")
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                flash('Login berhasil!', 'success')
                return redirect(url_for('index'))
            else:
                logger.debug("Password tidak cocok")
                flash('Password salah!', 'danger')
        else:
            logger.debug("User tidak ditemukan")
            flash('Username tidak ditemukan!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/estimasi', methods=['GET', 'POST'])
@login_required
def estimasi():
    if request.method == 'POST':
        try:
            # Validasi session
            if 'user_id' not in session:
                flash('Sesi Anda telah berakhir. Silakan login kembali.', 'danger')
                return redirect(url_for('login'))
            
            # Validasi input
            required_fields = ['nama', 'merk', 'tipe', 'ram', 'penyimpanan', 'tahun', 'harga_beli', 'kondisi']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Mohon isi {field.replace("_", " ").title()}', 'danger')
                    return redirect(url_for('estimasi'))
            
            # Ambil dan bersihkan data input
            nama = request.form['nama'].strip()
            merk = request.form['merk'].strip()
            tipe = request.form['tipe'].strip()
            
            try:
                ram = int(request.form['ram'])
                penyimpanan = int(request.form['penyimpanan'])
                tahun = int(request.form['tahun'])
                harga_beli = float(request.form['harga_beli'].replace('.', '').replace(',', ''))
            except ValueError as e:
                logger.error(f"Error konversi nilai: {str(e)}")
                flash('Mohon masukkan nilai yang valid untuk RAM, Penyimpanan, Tahun, dan Harga Beli', 'danger')
                return redirect(url_for('estimasi'))
            
            kondisi = request.form['kondisi'].strip()
            
            # Validasi nilai numerik
            current_year = datetime.now().year
            if ram < 1:
                flash('RAM minimal 1 GB', 'danger')
                return redirect(url_for('estimasi'))
            if penyimpanan < 1:
                flash('Penyimpanan minimal 1 GB', 'danger')
                return redirect(url_for('estimasi'))
            if tahun < 2010 or tahun > current_year:
                flash(f'Tahun keluaran harus antara 2010-{current_year}', 'danger')
                return redirect(url_for('estimasi'))
            if harga_beli <= 0:
                flash('Harga beli harus lebih dari 0', 'danger')
                return redirect(url_for('estimasi'))
            
            # Inisialisasi variabel
            estimasi = 0
            estimasi_min = None
            estimasi_max = None
            is_from_history = False
            
            # Cari di data historis
            logger.info(f"Mencari data historis untuk: {merk} {tipe}")
            data_historis = DataHistorisHP.query.filter_by(
                merk_hp=merk,
                tipe_hp=tipe
            ).first()
            
            if data_historis:
                logger.info(f"Data historis ditemukan: {data_historis.nilai_gadai}")
                # Kalkulasi berdasarkan data historis
                nilai_historis = float(data_historis.nilai_gadai)
                # Sesuaikan dengan kondisi
                kondisi_persen = float(kondisi.replace('%', '')) / 100
                estimasi = nilai_historis * kondisi_persen * 0.7  # 70% dari nilai barang
                is_from_history = True
                estimasi_min = estimasi * 0.9  # 90% dari estimasi
                estimasi_max = estimasi * 1.1  # 110% dari estimasi
            else:
                logger.info("Data historis tidak ditemukan, mencari HP serupa")
                # Cari HP dengan spesifikasi serupa
                similar_phones = DataHistorisHP.query.filter(
                    DataHistorisHP.ram == ram,
                    DataHistorisHP.penyimpanan == penyimpanan,
                    DataHistorisHP.tahun_keluaran >= tahun - 1,
                    DataHistorisHP.tahun_keluaran <= tahun + 1
                ).all()
                
                if similar_phones:
                    logger.info(f"Ditemukan {len(similar_phones)} HP serupa")
                    nilai_min = min(float(phone.nilai_gadai) for phone in similar_phones)
                    nilai_max = max(float(phone.nilai_gadai) for phone in similar_phones)
                    estimasi = (nilai_min + nilai_max) / 2 * 0.7  # 70% dari rata-rata
                    estimasi_min = nilai_min * 0.7  # 70% dari nilai minimum
                    estimasi_max = nilai_max * 0.7  # 70% dari nilai maximum
                else:
                    logger.info("Tidak ada HP serupa, menggunakan harga beli")
                    # Jika tidak ada data serupa, gunakan harga beli sebagai patokan
                    estimasi = harga_beli * 0.5  # 50% dari harga beli
                    estimasi_min = estimasi * 0.8  # 80% dari estimasi
                    estimasi_max = estimasi * 1.2  # 120% dari estimasi
            
            # Buat objek gadai
            gadai = Gadai(
                nama_pemohon=nama,
                merk_hp=merk,
                tipe_hp=tipe,
                ram=ram,
                penyimpanan=penyimpanan,
                tahun_keluaran=tahun,
                harga_beli=harga_beli,
                kondisi=kondisi,
                estimasi_pinjaman=estimasi,
                estimasi_minimum=estimasi_min,
                estimasi_maximum=estimasi_max,
                is_from_history=is_from_history,
                user_id=session['user_id']
            )
            
            db.session.add(gadai)
            db.session.commit()
            logger.info(f"Estimasi berhasil disimpan dengan id: {gadai.id}")
            
            return redirect(url_for('hasil', id=gadai.id))
            
        except Exception as e:
            logger.error(f"Error saat memproses estimasi: {str(e)}")
            db.session.rollback()
            flash('Terjadi kesalahan saat memproses estimasi', 'danger')
            return redirect(url_for('estimasi'))
    
    return render_template('estimasi.html')

@app.route('/hasil/<int:id>')
@login_required
def hasil(id):
    try:
        logger.info(f"Mencoba mengambil data gadai dengan id: {id}")
        
        # Ambil data dari database dengan error handling yang lebih baik
        gadai = Gadai.query.get(id)
        if not gadai:
            logger.error(f"Data gadai dengan id {id} tidak ditemukan")
            flash('Data estimasi tidak ditemukan', 'danger')
            return redirect(url_for('estimasi'))
        
        # Pastikan pengguna memiliki akses ke data ini
        if gadai.user_id != session['user_id'] and session['role'] != 'admin':
            logger.warning(f"User {session['user_id']} mencoba mengakses data gadai {id} tanpa izin")
            flash('Anda tidak memiliki akses ke data ini', 'danger')
            return redirect(url_for('estimasi'))
        
        logger.info(f"Memformat data gadai untuk ditampilkan")
        
        # Konversi nilai ke format yang sesuai dengan penanganan error
        gadai_data = {
            'id': gadai.id,
            'nama_pemohon': gadai.nama_pemohon,
            'merk_hp': gadai.merk_hp,
            'tipe_hp': gadai.tipe_hp,
            'ram': gadai.ram,
            'penyimpanan': gadai.penyimpanan,
            'tahun_keluaran': gadai.tahun_keluaran,
            'kondisi': gadai.kondisi,
            'harga_beli': float(gadai.harga_beli),
            'estimasi_pinjaman': float(gadai.estimasi_pinjaman),
            'estimasi_minimum': float(gadai.estimasi_minimum) if gadai.estimasi_minimum else None,
            'estimasi_maximum': float(gadai.estimasi_maximum) if gadai.estimasi_maximum else None,
            'is_from_history': bool(gadai.is_from_history),
            'tanggal_gadai': gadai.tanggal_gadai.strftime('%d/%m/%Y %H:%M') if gadai.tanggal_gadai else None
        }
        
        logger.info(f"Data gadai berhasil diformat, menampilkan hasil")
        return render_template('hasil.html', gadai=gadai_data)
        
    except (ValueError, AttributeError) as e:
        logger.error(f"Error saat memformat data gadai: {str(e)}")
        flash('Terjadi kesalahan saat memformat data estimasi', 'danger')
        return redirect(url_for('estimasi'))
    except Exception as e:
        logger.error(f"Error saat menampilkan hasil estimasi: {str(e)}")
        flash('Terjadi kesalahan saat menampilkan hasil estimasi', 'danger')
        return redirect(url_for('estimasi'))

# Tambahkan route baru untuk membersihkan session saat kembali ke halaman estimasi
@app.route('/clear-estimasi')
@login_required
def clear_estimasi():
    # Hapus semua data estimasi dari session
    keys_to_remove = [key for key in session.keys() if key.startswith('estimasi_')]
    for key in keys_to_remove:
        session.pop(key, None)
    return redirect(url_for('estimasi'))

@app.route('/riwayat')
@login_required
@cache.memoize(timeout=60)
def riwayat():
    try:
        if session['role'] == 'admin':
            daftar_gadai = Gadai.query.order_by(Gadai.tanggal_gadai.desc()).all()
        else:
            daftar_gadai = Gadai.query.filter_by(user_id=session['user_id']).order_by(Gadai.tanggal_gadai.desc()).all()
        return render_template('riwayat.html', daftar_gadai=daftar_gadai)
    except Exception as e:
        logger.error(f"Error pada halaman riwayat: {str(e)}")
        flash('Terjadi kesalahan saat memuat riwayat', 'danger')
        return redirect(url_for('index'))

@app.route('/create-admin')
def create_admin():
    try:
        # Hapus admin yang ada jika ada masalah
        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin:
            # Hapus dulu semua data gadai yang terkait dengan admin
            Gadai.query.filter_by(user_id=existing_admin.id).delete()
            db.session.commit()
            logger.debug("Data gadai terkait admin dihapus")
            
            # Baru hapus admin
            db.session.delete(existing_admin)
            db.session.commit()
            logger.debug("Admin lama dihapus")
        
        # Buat admin baru dengan password yang benar
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        admin = User(
            username='admin',
            password=hashed_password,
            nama_lengkap='Administrator',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        logger.debug(f"Admin baru dibuat dengan password hash: {hashed_password}")
        flash('Admin berhasil dibuat! Username: admin, Password: admin123', 'success')
    except Exception as e:
        logger.error(f"Error saat membuat admin: {str(e)}")
        db.session.rollback()
        flash('Terjadi kesalahan saat membuat admin', 'danger')
    return redirect(url_for('login'))

@app.route('/debug-users')
def debug_users():
    try:
        users = User.query.all()
        result = []
        for user in users:
            result.append({
                'username': user.username,
                'password_hash': user.password,
                'role': user.role
            })
        return {'users': result}
    except Exception as e:
        return {'error': str(e)}

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nama_lengkap = request.form['nama_lengkap']
        
        # Cek apakah username sudah ada
        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan!', 'danger')
            return redirect(url_for('register'))
        
        # Buat user baru dengan role 'user'
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, nama_lengkap=nama_lengkap, role='user')
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Terjadi kesalahan saat registrasi. Silakan coba lagi.', 'danger')
            logger.error(f"Error saat registrasi: {str(e)}")
    
    return render_template('register.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Route untuk Panduan
@app.route('/panduan')
def panduan():
    return render_template('panduan.html')

# Route untuk Hubungi Kami
@app.route('/kontak', methods=['GET', 'POST'])
def kontak():
    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        pesan = request.form['pesan']
        # TODO: Implementasi pengiriman email atau penyimpanan pesan kontak
        flash('Pesan Anda telah terkirim! Kami akan menghubungi Anda segera.', 'success')
        return redirect(url_for('kontak'))
    return render_template('kontak.html')

# Route untuk Tentang
@app.route('/tentang')
def tentang():
    return render_template('tentang.html')

# Route untuk Profil
@app.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    user = User.query.get(session['user_id'])
    
    # Hitung statistik
    total_estimasi = Gadai.query.filter_by(user_id=user.id).count()
    
    # Hitung estimasi bulan ini
    now = datetime.now(timezone.utc)
    awal_bulan = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    estimasi_bulan_ini = Gadai.query.filter(
        Gadai.user_id == user.id,
        Gadai.tanggal_gadai >= awal_bulan
    ).count()
    
    # Hitung estimasi dalam proses
    estimasi_proses = Gadai.query.filter(
        Gadai.user_id == user.id,
        Gadai.status == 'pending'
    ).count()
    
    # Ambil 5 estimasi terbaru
    estimasi_terbaru = Gadai.query.filter_by(user_id=user.id)\
        .order_by(Gadai.tanggal_gadai.desc())\
        .limit(5)\
        .all()
    
    # Hitung statistik per status
    status_stats = {
        'pending': Gadai.query.filter_by(user_id=user.id, status='pending').count(),
        'verified': Gadai.query.filter_by(user_id=user.id, status='verified').count(),
        'rejected': Gadai.query.filter_by(user_id=user.id, status='rejected').count()
    }
    
    if request.method == 'POST':
        nama_lengkap_baru = request.form.get('nama_lengkap', '').strip()
        if nama_lengkap_baru:
            user.nama_lengkap = nama_lengkap_baru
            db.session.commit()
            flash('Nama lengkap berhasil diperbarui!', 'success')
            return redirect(url_for('profil'))
        else:
            flash('Nama lengkap tidak boleh kosong.', 'danger')
            
    return render_template('profil.html', 
                         user=user,
                         total_estimasi=total_estimasi,
                         estimasi_bulan_ini=estimasi_bulan_ini,
                         estimasi_proses=estimasi_proses,
                         estimasi_terbaru=estimasi_terbaru,
                         status_stats=status_stats)

# Route untuk Ubah Password
@app.route('/ubah-password', methods=['GET', 'POST'])
@login_required
def ubah_password():
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if not check_password_hash(user.password, old_password):
            flash('Password lama tidak sesuai!', 'danger')
        elif new_password != confirm_password:
            flash('Password baru dan konfirmasi tidak cocok!', 'danger')
        else:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password berhasil diubah!', 'success')
            return redirect(url_for('profil'))
    return render_template('ubah_password.html')

@app.route('/admin/estimasi')
@login_required
@admin_required
def admin_estimasi():
    if session.get('role') != 'admin':
        flash('Anda tidak memiliki akses ke halaman ini', 'danger')
        return redirect(url_for('index'))
    estimasi_list = Gadai.query.order_by(Gadai.tanggal_gadai.desc()).all()
    return render_template('admin/estimasi.html', estimasi_list=estimasi_list)

@app.route('/admin/verifikasi')
@login_required
@admin_required
def admin_verifikasi():
    if session.get('role') != 'admin':
        flash('Anda tidak memiliki akses ke halaman ini', 'danger')
        return redirect(url_for('index'))
    pengajuan_pending = Gadai.query.filter_by(status='pending').order_by(Gadai.tanggal_gadai.desc()).all()
    return render_template('admin/verifikasi.html', pengajuan_pending=pengajuan_pending)

@app.route('/admin/verifikasi/setuju/<int:id>', methods=['POST'])
@login_required
@admin_required
def verifikasi_setuju(id):
    try:
        estimasi = Gadai.query.get_or_404(id)
        if estimasi.status != 'pending':
            return jsonify({'success': False, 'error': 'Estimasi sudah diverifikasi'})
            
        # Ambil data dari request
        data = request.get_json()
        
        # Update status dan informasi verifikasi
        estimasi.status = 'verified'
        estimasi.catatan_verifikasi = data.get('catatan', '')
        estimasi.tanggal_verifikasi = datetime.now(timezone.utc)
        estimasi.verifikator_id = session['user_id']
        
        try:
            db.session.commit()
            # Hapus cache riwayat
            cache.delete_memoized(riwayat)
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saat menyimpan verifikasi: {str(e)}")
            return jsonify({'success': False, 'error': 'Gagal menyimpan verifikasi'})
            
    except Exception as e:
        logger.error(f"Error pada verifikasi_setuju: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/verifikasi/tolak/<int:id>', methods=['POST'])
@login_required
@admin_required
def verifikasi_tolak(id):
    try:
        estimasi = Gadai.query.get_or_404(id)
        if estimasi.status != 'pending':
            return jsonify({'success': False, 'error': 'Estimasi sudah diverifikasi'})
            
        # Ambil data dari request
        data = request.get_json()
        
        # Update status dan informasi verifikasi
        estimasi.status = 'rejected'
        estimasi.catatan_verifikasi = data.get('alasan', '')
        estimasi.tanggal_verifikasi = datetime.now(timezone.utc)
        estimasi.verifikator_id = session['user_id']
        
        try:
            db.session.commit()
            # Hapus cache riwayat
            cache.delete_memoized(riwayat)
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saat menyimpan penolakan: {str(e)}")
            return jsonify({'success': False, 'error': 'Gagal menyimpan penolakan'})
            
    except Exception as e:
        logger.error(f"Error pada verifikasi_tolak: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Route untuk Admin - Statistik
@app.route('/admin/statistik')
@login_required
@admin_required
def admin_statistik():
    if session.get('role') != 'admin':
        flash('Anda tidak memiliki akses ke halaman ini', 'danger')
        return redirect(url_for('index'))

    try:
        # Menggunakan datetime.now(timezone.utc) untuk konsistensi
        now = datetime.now(timezone.utc)
        
        # Statistik harian (7 hari terakhir)
        daily_stats = []
        for i in range(7):
            start_date = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            count = Gadai.query.filter(
                Gadai.tanggal_gadai >= start_date,
                Gadai.tanggal_gadai < end_date
            ).count()
            daily_stats.append({
                'date': start_date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        # Statistik dasar
        total_estimasi = Gadai.query.count()
        estimasi_disetujui = Gadai.query.filter_by(status='verified').count()
        estimasi_pending = Gadai.query.filter_by(status='pending').count()
        
        # Hitung rata-rata pinjaman yang disetujui
        avg_result = db.session.query(
            db.func.avg(Gadai.estimasi_pinjaman).label('avg_pinjaman')
        ).filter(
            Gadai.status == 'verified'
        ).first()
        rata_pinjaman = float(avg_result.avg_pinjaman) if avg_result.avg_pinjaman else 0
        
        # Top 5 estimasi tertinggi
        top_estimasi = Gadai.query.order_by(
            Gadai.estimasi_pinjaman.desc()
        ).limit(5).all()
        
        # Statistik bulanan (6 bulan terakhir)
        statistik_bulanan = []
        current_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(6):
            if i == 0:
                start_date = current_date
            else:
                if current_date.month == 1:
                    start_date = current_date.replace(year=current_date.year - 1, month=12)
                else:
                    start_date = current_date.replace(month=current_date.month - 1)
            
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1)
            
            monthly_data = Gadai.query.filter(
                Gadai.tanggal_gadai >= start_date,
                Gadai.tanggal_gadai < end_date
            )
            
            total = monthly_data.count()
            disetujui = monthly_data.filter_by(status='verified').count()
            
            avg_result = db.session.query(
                db.func.avg(Gadai.estimasi_pinjaman).label('avg_pinjaman')
            ).filter(
                Gadai.tanggal_gadai >= start_date,
                Gadai.tanggal_gadai < end_date
            ).first()
            rata_rata = float(avg_result.avg_pinjaman) if avg_result.avg_pinjaman else 0
            
            statistik_bulanan.append({
                'bulan': start_date.strftime('%b %Y'),
                'total': total,
                'disetujui': disetujui,
                'rata_rata': rata_rata
            })
            
            current_date = start_date
        
        # Balik urutan statistik bulanan agar yang terbaru di atas
        statistik_bulanan.reverse()
        
        return render_template(
            'admin/statistik.html',
            total_estimasi=total_estimasi,
            estimasi_disetujui=estimasi_disetujui,
            estimasi_pending=estimasi_pending,
            rata_pinjaman=rata_pinjaman,
            persentase_disetujui=round((estimasi_disetujui / total_estimasi * 100) if total_estimasi > 0 else 0, 1),
            top_estimasi=top_estimasi,
            statistik_bulanan=statistik_bulanan,
            daily_stats=daily_stats
        )
        
    except Exception as e:
        logger.error(f"Error pada halaman statistik: {str(e)}")
        flash('Terjadi kesalahan saat memuat statistik', 'danger')
        return redirect(url_for('index'))

@app.route('/api/estimasi/<int:id>')
@login_required
def api_estimasi_detail(id):
    estimasi = Gadai.query.get_or_404(id)
    
    # Pastikan pengguna memiliki akses ke data ini
    if session['role'] != 'admin' and estimasi.user_id != session['user_id']:
        return {'error': 'Tidak memiliki akses'}, 403
    
    # Ambil data verifikator jika ada
    verifikator = None
    if estimasi.verifikator_id:
        verifikator = User.query.get(estimasi.verifikator_id)
    
    return {
        'id': estimasi.id,
        'nama_pemohon': estimasi.nama_pemohon,
        'merk_hp': estimasi.merk_hp,
        'tipe_hp': estimasi.tipe_hp,
        'ram': estimasi.ram,
        'penyimpanan': estimasi.penyimpanan,
        'tahun_keluaran': estimasi.tahun_keluaran,
        'kondisi': estimasi.kondisi,
        'estimasi_pinjaman': float(estimasi.estimasi_pinjaman),
        'tanggal_gadai': estimasi.tanggal_gadai.strftime('%d/%m/%Y %H:%M'),
        'status': estimasi.status,
        'catatan_verifikasi': estimasi.catatan_verifikasi,
        'tanggal_verifikasi': estimasi.tanggal_verifikasi.strftime('%d/%m/%Y %H:%M') if estimasi.tanggal_verifikasi else None,
        'verifikator': verifikator.nama_lengkap if verifikator else None
    }

@app.route('/simpan_estimasi', methods=['POST'])
def simpan_estimasi():
    try:
        data = request.get_json()
        
        # Validasi dan konversi data
        try:
            ram = int(str(data.get('ram', '')).strip())
            penyimpanan = int(str(data.get('penyimpanan', '')).strip())
            tahun = int(str(data.get('tahun', '')).strip())
            harga_beli = float(str(data.get('harga_beli', '0')).replace(',', '').strip())
            estimasi_pinjaman = float(str(data.get('estimasi_pinjaman', '0')).strip())
        except ValueError as e:
            return jsonify({
                'status': 'error',
                'message': f'Format data tidak valid: {str(e)}'
            }), 400
        
        # Validasi nilai
        if ram <= 0 or penyimpanan <= 0 or tahun < 2010 or harga_beli <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Nilai RAM, penyimpanan, tahun, atau harga beli tidak valid'
            }), 400
        
        estimasi = Estimasi(
            nama_pemohon=str(data.get('nama', '')).strip(),
            merk_hp=str(data.get('merk', '')).strip(),
            tipe_hp=str(data.get('tipe', '')).strip(),
            ram=ram,
            penyimpanan=penyimpanan,
            tahun_keluaran=tahun,
            harga_beli=harga_beli,
            kondisi=str(data.get('kondisi', '')).strip(),
            estimasi_pinjaman=estimasi_pinjaman,
            status='Menunggu Persetujuan'
        )
        
        db.session.add(estimasi)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Data telah disimpan',
            'id': estimasi.id
        })
    except Exception as e:
        logger.error(f"Error saat menyimpan estimasi: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@app.route('/admin/estimasi/<int:id>/update_status', methods=['POST'])
def update_status_estimasi(id):
    estimasi = Estimasi.query.get_or_404(id)
    data = request.get_json()
    
    estimasi.status = data['status']
    estimasi.catatan_admin = data.get('catatan', '')
    estimasi.tanggal_persetujuan = datetime.utcnow() if data['status'] == 'Disetujui' else None
    
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/manajemen')
@login_required
@admin_required
def admin_manajemen():
    if session.get('role') != 'admin':
        flash('Anda tidak memiliki akses ke halaman ini', 'danger')
        return redirect(url_for('index'))
    data_barang = DataBarangReferensi.query.order_by(DataBarangReferensi.updated_at.desc()).all()
    return render_template('admin/manajemen_data.html', data_barang=data_barang)

@app.route('/admin/manajemen/get_barang/<int:id>')
@login_required
@admin_required
def get_barang(id):
    barang = DataBarangReferensi.query.get_or_404(id)
    return jsonify({
        'id': barang.id,
        'merk': barang.merk,
        'tipe': barang.tipe,
        'ram': barang.ram,
        'penyimpanan': barang.penyimpanan,
        'tahun_rilis': barang.tahun_rilis,
        'harga_pasar': barang.harga_pasar
    })

@app.route('/admin/manajemen/tambah', methods=['POST'])
@login_required
@admin_required
def tambah_barang():
    try:
        barang = DataBarangReferensi(
            merk=request.form['merk'],
            tipe=request.form['tipe'],
            ram=int(request.form['ram']),
            penyimpanan=int(request.form['penyimpanan']),
            tahun_rilis=int(request.form['tahun_rilis']),
            harga_pasar=float(request.form['harga_pasar'])
        )
        db.session.add(barang)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/manajemen/update/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_barang(id):
    try:
        barang = DataBarangReferensi.query.get_or_404(id)
        barang.merk = request.form['merk']
        barang.tipe = request.form['tipe']
        barang.ram = int(request.form['ram'])
        barang.penyimpanan = int(request.form['penyimpanan'])
        barang.tahun_rilis = int(request.form['tahun_rilis'])
        barang.harga_pasar = float(request.form['harga_pasar'])
        barang.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/manajemen/hapus/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def hapus_barang(id):
    try:
        barang = DataBarangReferensi.query.get_or_404(id)
        db.session.delete(barang)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/manajemen/export_excel')
@login_required
@admin_required
def export_barang_excel():
    try:
        # Query data barang referensi
        data = DataBarangReferensi.query.order_by(DataBarangReferensi.updated_at.desc()).all()
        # Siapkan data untuk DataFrame
        rows = []
        for barang in data:
            rows.append({
                'ID': barang.id,
                'Merk': barang.merk,
                'Tipe': barang.tipe,
                'RAM (GB)': barang.ram,
                'Penyimpanan (GB)': barang.penyimpanan,
                'Tahun Rilis': barang.tahun_rilis,
                'Harga Pasar (Rp)': barang.harga_pasar,
                'Terakhir Update': barang.updated_at.strftime('%Y-%m-%d %H:%M') if barang.updated_at else ''
            })
        df = pd.DataFrame(rows)
        # Simpan ke file Excel di memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='DataBarang')
        output.seek(0)
        # Kirim file ke user
        return send_file(output, download_name='data_barang_referensi.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f'Gagal export data: {str(e)}', 500

@app.route('/admin/manajemen/import_excel', methods=['POST'])
@login_required
@admin_required
def import_barang_excel():
    if 'file_excel' not in request.files:
        flash('File tidak ditemukan!', 'danger')
        return redirect(url_for('admin_manajemen'))
    file = request.files['file_excel']
    if file.filename == '':
        flash('File tidak dipilih!', 'danger')
        return redirect(url_for('admin_manajemen'))
    if not file.filename.endswith('.xlsx'):
        flash('Format file harus .xlsx', 'danger')
        return redirect(url_for('admin_manajemen'))
    try:
        df = pd.read_excel(file)
        # Mapping kolom sesuai format
        df = df.rename(columns={
            'Merk HP': 'merk',
            'Tipe HP': 'tipe',
            'RAM (GB)': 'ram',
            'Penyimpanan (GB)': 'penyimpanan',
            'Tahun Keluaran': 'tahun_rilis',
            'Nilai Gadai': 'harga_pasar'
        })
        # Hanya ambil kolom yang dibutuhkan
        kolom_wajib = ['merk', 'tipe', 'ram', 'penyimpanan', 'tahun_rilis', 'harga_pasar']
        if not all(k in df.columns for k in kolom_wajib):
            flash('Format kolom tidak sesuai template!', 'danger')
            return redirect(url_for('admin_manajemen'))
        # Tambahkan ke database
        count = 0
        for _, row in df.iterrows():
            barang = DataBarangReferensi(
                merk=str(row['merk']),
                tipe=str(row['tipe']),
                ram=int(row['ram']),
                penyimpanan=int(row['penyimpanan']),
                tahun_rilis=int(row['tahun_rilis']),
                harga_pasar=float(row['harga_pasar'])
            )
            db.session.add(barang)
            count += 1
        db.session.commit()
        flash(f'Berhasil mengimport {count} data barang!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal import data: {str(e)}', 'danger')
    return redirect(url_for('admin_manajemen'))

# Tambahkan fungsi untuk membuat database
def init_db():
    with app.app_context():
        # Hapus semua tabel yang ada
        db.drop_all()
        # Buat ulang semua tabel
        db.create_all()
        # Buat admin default
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            nama_lengkap='Administrator',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        try:
            # Cek koneksi database
            db.session.execute(text('SELECT 1'))
            print("Koneksi database berhasil")
            
            # Pastikan tabel ada
            db.create_all()
            print("Struktur database siap")
            
        except Exception as e:
            print(f"Error saat inisialisasi database: {str(e)}")
            import sys
            sys.exit(1)
    
    # Jalankan aplikasi
    app.run(debug=False, port=5000, threaded=True) 