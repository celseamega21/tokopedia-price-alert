import pytest
from unittest.mock import patch, Mock
from core.models import PriceHistory, Product
from .tasks import check_price
from scraper.utils import clean_price

@patch('scraper.tasks.send_mail')
@patch('scraper.tasks.Scraper')
@pytest.mark.django_db
def test_check_price_decrease(mock_scraper, mock_send_mail, product, scraper_engine):
    product.engine = scraper_engine
    product.last_price = 160000
    product.save()

    mock_instance = Mock()
    mock_instance.scrape_product.return_value = {
        "product_name": "Test Product",
        "discount_price": "Rp100.000"
    }
    mock_scraper.return_value = mock_instance
    mock_send_mail.return_value = 1

    check_price(scraper_engine.id)

    product.refresh_from_db()
    assert product.last_price == 100000

    history = PriceHistory.objects.filter(product=product, price=100000).first()
    assert history is not None

    assert Product.objects.filter(engine=scraper_engine).exists()

    mock_send_mail.assert_called_once()

@patch('scraper.tasks.Scraper')
@pytest.mark.django_db
def test_check_price_not_decrease(mock_scraper, product):
    product.last_price = 150000
    product.save()

    mock_instance = Mock()
    mock_instance.scrape_product.return_value = {
        "product_name": "Test Product",
        "discount_price": 160000
    }
    mock_scraper.return_value = mock_instance

    engine = product.engine
    original_count = engine.task_count

    product.refresh_from_db()
    engine.refresh_from_db()

    assert product.last_price == 150000
    assert PriceHistory.objects.filter(product=product).count() == 0
    assert engine.task_count == max(original_count - 1, 0)

def test_clean_price():
    assert clean_price("Rp2.989.000") == 2989000
    assert clean_price("Rp2,989,000") == 2989000
    assert clean_price(2989000) == 2989000
    assert clean_price("Rp 2.989.000") == 2989000
    assert clean_price(0) == 0
    assert clean_price(None) == 0
    assert clean_price("test") == 0