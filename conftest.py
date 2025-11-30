import pytest
from account.models import User
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from scraper.models import ScraperEngine
from core.models import Product
from scraper.models import ScraperEngine

@pytest.fixture
def user(db):
    user = User.objects.create_user(username="test", email="test@example.com", password="testpassword123")
    return user

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def refresh_url():
    return reverse('account:token_obtain_pair')

@pytest.fixture
def auth_client(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client

@pytest.fixture
def scraper_engine(db):
    return ScraperEngine.objects.create(
        engine_name='Test Engine',
        task_count=0,
        active=True,
        ip_engine='127.0.0.1',
        port=8080
    )

@pytest.fixture
def product(db, user, scraper_engine):
    return Product.objects.create(
        user=user,
        email='test@example.com',
        name='Test Product',
        url='http://example.com/product',
        engine=scraper_engine,
        last_price=150000,
    )