import pytest
from flask import session
from app import app, db, User, Gadai
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            # Bersihkan database
            db.drop_all()
            db.create_all()
            
            # Buat user test
            user = User(
                username='testuser',
                password=generate_password_hash('test123'),
                nama_lengkap='Test User',
                role='user'
            )
            db.session.add(user)
            db.session.commit()
            
            # Login user
            with client.session_transaction() as sess:
                sess['user_id'] = user.id
                sess['username'] = user.username
                sess['role'] = user.role
                
        yield client

def test_estimasi_page(client, regular_user):
    """Test akses halaman estimasi"""
    with client.application.app_context():
        # Login dulu
        client.post('/login', data={
            'username': 'user',
            'password': 'user123'
        })
        
        response = client.get('/estimasi')
        assert response.status_code == 200
        assert b'Form Estimasi Gadai' in response.data

def test_estimasi_validation(client, regular_user):
    """Test validasi form estimasi"""
    with client.application.app_context():
        # Login dulu
        client.post('/login', data={
            'username': 'user',
            'password': 'user123'
        })
        
        response = client.post('/estimasi', data={}, follow_redirects=True)
        assert response.status_code == 200
        assert b'Mohon lengkapi semua field yang diperlukan' in response.data

def test_estimasi_success(client, regular_user):
    """Test estimasi berhasil"""
    with client.application.app_context():
        # Login dulu
        client.post('/login', data={
            'username': 'user',
            'password': 'user123'
        })
        
        response = client.post('/estimasi', data={
            'nama_pemohon': 'Test User',
            'merk_hp': 'Samsung',
            'tipe_hp': 'Galaxy S21',
            'ram': '8',
            'penyimpanan': '128',
            'tahun_keluaran': '2021',
            'harga_beli': '10000000',
            'kondisi': '90%'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Estimasi berhasil disimpan' in response.data
        
        # Verifikasi data di database
        gadai = Gadai.query.filter_by(nama_pemohon='Test User').first()
        assert gadai is not None
        assert gadai.merk_hp == 'Samsung'
        assert gadai.tipe_hp == 'Galaxy S21'
        assert gadai.ram == 8
        assert gadai.penyimpanan == 128
        assert gadai.tahun_keluaran == 2021
        assert gadai.harga_beli == 10000000
        assert gadai.kondisi == '90%'
        assert gadai.status == 'pending'

def test_hasil_estimasi(client, regular_user):
    """Test halaman hasil estimasi"""
    with client.application.app_context():
        # Login dulu
        client.post('/login', data={
            'username': 'user',
            'password': 'user123'
        })
        
        # Buat estimasi
        gadai = Gadai(
            nama_pemohon='Test User',
            merk_hp='Samsung',
            tipe_hp='Galaxy S21',
            ram=8,
            penyimpanan=128,
            tahun_keluaran=2021,
            harga_beli=10000000,
            kondisi='90%',
            estimasi_pinjaman=7000000,
            user_id=regular_user.id,
            status='pending',
            tanggal_gadai=datetime.now(timezone.utc)
        )
        db.session.add(gadai)
        db.session.commit()
        
        response = client.get(f'/hasil-estimasi/{gadai.id}')
        assert response.status_code == 200
        assert b'Samsung Galaxy S21' in response.data
        assert b'Rp 7.000.000' in response.data

def test_riwayat_estimasi(client, regular_user):
    """Test halaman riwayat estimasi"""
    with client.application.app_context():
        # Login dulu
        client.post('/login', data={
            'username': 'user',
            'password': 'user123'
        })
        
        response = client.get('/riwayat')
        assert response.status_code == 200
        assert b'Riwayat Estimasi' in response.data 