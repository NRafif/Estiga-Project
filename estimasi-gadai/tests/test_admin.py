import pytest
from flask import session
from app import app, db, User, Gadai
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

@pytest.fixture
def admin_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            # Bersihkan database
            db.drop_all()
            db.create_all()
            
            # Buat admin test
            admin = User(
                username='testadmin',
                password=generate_password_hash('test123'),
                nama_lengkap='Test Admin',
                role='admin'
            )
            
            # Buat user biasa
            user = User(
                username='testuser',
                password=generate_password_hash('test123'),
                nama_lengkap='Test User',
                role='user'
            )
            
            db.session.add(admin)
            db.session.add(user)
            db.session.commit()
            
            # Login sebagai admin
            with client.session_transaction() as sess:
                sess['user_id'] = admin.id
                sess['username'] = admin.username
                sess['role'] = admin.role
                
        yield client

def test_admin_verifikasi_page(client, admin_user):
    """Test akses halaman verifikasi admin"""
    with client.application.app_context():
        # Login sebagai admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get('/admin/verifikasi')
        assert response.status_code == 200
        assert b'Verifikasi Estimasi' in response.data

def test_admin_verifikasi_setuju(client, admin_user):
    """Test admin menyetujui estimasi"""
    with client.application.app_context():
        # Login sebagai admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        # Buat data gadai untuk diverifikasi
        gadai = Gadai(
            nama_pemohon='Test User',
            merk_hp='Samsung',
            tipe_hp='Galaxy S21',
            ram=8,
            penyimpanan=128,
            tahun_keluaran=2021,
            harga_beli=10000000,
            kondisi='90%',
            estimasi_pinjaman=5000000,
            user_id=admin_user.id,
            status='pending',
            tanggal_gadai=datetime.now(timezone.utc)
        )
        db.session.add(gadai)
        db.session.commit()

        response = client.post(f'/admin/verifikasi/{gadai.id}/setuju', follow_redirects=True)
        assert response.status_code == 200
        assert b'Estimasi berhasil diverifikasi' in response.data

        # Verifikasi status di database
        gadai = db.session.get(Gadai, gadai.id)
        assert gadai.status == 'approved'

def test_admin_verifikasi_tolak(client, admin_user):
    """Test admin menolak estimasi"""
    with client.application.app_context():
        # Login sebagai admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        # Buat data gadai untuk diverifikasi
        gadai = Gadai(
            nama_pemohon='Test User',
            merk_hp='Samsung',
            tipe_hp='Galaxy S21',
            ram=8,
            penyimpanan=128,
            tahun_keluaran=2021,
            harga_beli=10000000,
            kondisi='90%',
            estimasi_pinjaman=5000000,
            user_id=admin_user.id,
            status='pending',
            tanggal_gadai=datetime.now(timezone.utc)
        )
        db.session.add(gadai)
        db.session.commit()

        response = client.post(f'/admin/verifikasi/{gadai.id}/tolak', follow_redirects=True)
        assert response.status_code == 200
        assert b'Estimasi ditolak' in response.data

        # Verifikasi status di database
        gadai = db.session.get(Gadai, gadai.id)
        assert gadai.status == 'rejected'

def test_admin_statistik(client, admin_user):
    """Test halaman statistik admin"""
    with client.application.app_context():
        # Login sebagai admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get('/admin/statistik')
        assert response.status_code == 200
        assert b'Statistik Estimasi' in response.data

def test_non_admin_access(client, regular_user):
    """Test akses halaman admin oleh non-admin"""
    with client.application.app_context():
        # Login sebagai user biasa
        client.post('/login', data={
            'username': 'user',
            'password': 'user123'
        })

        response = client.get('/admin/verifikasi')
        assert response.status_code == 302  # Redirect ke halaman utama 