import pytest
from unittest.mock import patch, Mock
from django.urls import reverse
from core.models import Product, PriceHistory

@patch('core.views.check_price.delay')
@patch('core.views.Scraper')
@patch('core.views.LoadBalancer.get_scraper_engine')
@pytest.mark.django_db
def test_create_product(mock_get_engine, mock_scraper, mock_delay, auth_client, user, scraper_engine):
    scraper_engine.active = True
    mock_get_engine.return_value = scraper_engine
    scraper_instance = Mock()
    scraper_instance.scrape_product.return_value = {
        "product_name": "Test Product",
        "discount_price": "100000"
    }
    mock_scraper.return_value = scraper_instance

    data = {
        'url': 'http://example.com/product',
        'email': 'user@gmail.com'
    }

    response = auth_client.post(reverse('core:product-list'), data, format='json')
    assert response.status_code == 201
    assert response.data["message"] == "Product was successfully tracked!"

    product = Product.objects.get(url='http://example.com/product')
    assert product.user == user
    assert product.email == "user@gmail.com"
    assert product.name == "Test Product"
    assert product.url == "http://example.com/product"
    assert product.engine == scraper_engine
    assert product.last_price == 100000

    price_history = PriceHistory.objects.get(product=product)
    assert price_history.price == 100000

    mock_delay.assert_called_once_with(product.id)
    mock_scraper.assert_called_once_with("http://example.com/product")
    scraper_instance.scrape_product.assert_called_once()