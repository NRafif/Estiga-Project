import pytest
from app import db, User, Gadai
from datetime import datetime, timezone, timedelta

def test_profil_page(client, regular_user):
    """Test akses halaman profil"""
    with client.application.app_context():
        response = client.get('/profil')
        assert response.status_code == 200
        assert b'Profil Pengguna' in response.data

def test_update_profil(client, regular_user):
    """Test update profil"""
    with client.application.app_context():
        response = client.post('/profil/update', data={
            'nama_lengkap': 'Updated User',
            'username': 'user'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Nama lengkap berhasil diperbarui' in response.data
        
        # Verifikasi data di database
        user = db.session.get(User, regular_user.id)
        assert user.nama_lengkap == 'Updated User'

def test_profil_statistics(client, regular_user):
    """Test statistik profil"""
    with client.application.app_context():
        # Estimasi bulan ini
        estimasi1 = Gadai(
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
        db.session.add(estimasi1)
        
        # Estimasi bulan lalu
        estimasi2 = Gadai(
            nama_pemohon='Test User',
            merk_hp='iPhone',
            tipe_hp='13 Pro',
            ram=6,
            penyimpanan=256,
            tahun_keluaran=2021,
            harga_beli=15000000,
            kondisi='95%',
            estimasi_pinjaman=10000000,
            user_id=regular_user.id,
            status='approved',
            tanggal_gadai=datetime.now(timezone.utc) - timedelta(days=35)
        )
        db.session.add(estimasi2)
        db.session.commit()
        
        response = client.get('/profil')
        assert response.status_code == 200
        assert b'Total Estimasi: 2' in response.data
        assert b'Estimasi Bulan Ini: 1' in response.data
        assert b'Estimasi Bulan Lalu: 1' in response.data

def test_ubah_password(client, regular_user):
    """Test ubah password"""
    with client.application.app_context():
        response = client.post('/profil/ubah-password', data={
            'password_lama': 'user123',
            'password_baru': 'newpass123',
            'konfirmasi_password': 'newpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Password berhasil diubah' in response.data
        
        # Verifikasi password baru
        response = client.post('/login', data={
            'username': 'user',
            'password': 'newpass123'
        })
        assert response.status_code == 302  # Redirect ke halaman utama 