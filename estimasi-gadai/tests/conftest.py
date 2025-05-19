import os
import pytest
from app import app, db, User
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        client = app.test_client()
        yield client
        db.session.remove()
        db.drop_all()

@pytest.fixture
def regular_user(client):
    with app.app_context():
        # Hapus user yang sudah ada
        User.query.delete()
        db.session.commit()
        
        # Buat user baru
        user = User(
            username='user',
            password='user123',
            nama_lengkap='Test User',
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        
        # Login user
        client.post('/login', data={
            'username': 'user',
            'password': 'user123'
        })
        return user

@pytest.fixture
def admin_user(client):
    with app.app_context():
        # Hapus user yang sudah ada
        User.query.delete()
        db.session.commit()
        
        # Buat admin baru
        admin = User(
            username='admin',
            password='admin123',
            nama_lengkap='Admin User',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        
        # Login admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        return admin

@pytest.fixture
def auth_client(client):
    client.post('/login', data={
        'username': 'testuser',
        'password': 'test123'
    })
    return client

@pytest.fixture
def admin_client(client):
    client.post('/login', data={
        'username': 'testadmin',
        'password': 'test123'
    })
    return client 