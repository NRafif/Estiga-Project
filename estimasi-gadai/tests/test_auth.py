import pytest
from flask import session
from app import User, db
from werkzeug.security import generate_password_hash, check_password_hash

def test_login_success(client, regular_user):
    """Test login berhasil"""
    with client.session_transaction() as session:
        session.clear()
        
    response = client.post('/login', data={
        'username': 'user',
        'password': 'user123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Login berhasil' in response.data

def test_login_failure(client, regular_user):
    """Test login gagal"""
    with client.session_transaction() as session:
        session.clear()
        
    response = client.post('/login', data={
        'username': 'user',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 200
    assert b'Password salah' in response.data

def test_register_success(client):
    """Test registrasi berhasil"""
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'newpass123',
        'nama_lengkap': 'New User'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Registrasi berhasil' in response.data

def test_register_duplicate_username(client, regular_user):
    """Test registrasi dengan username yang sudah ada"""
    response = client.post('/register', data={
        'username': 'user',
        'password': 'pass123',
        'nama_lengkap': 'Another User'
    })
    
    assert response.status_code == 200
    assert b'Username sudah digunakan' in response.data

def test_logout(client, regular_user):
    """Test logout"""
    # Login dulu
    client.post('/login', data={
        'username': 'user',
        'password': 'user123'
    })
    
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Anda telah logout' in response.data 