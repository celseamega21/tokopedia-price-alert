from celery import shared_task
from django.core.mail import send_mail
from celery.utils.log import get_task_logger
from .scraper import Scraper
from core.models import PriceHistory, Product
from .load_balancer import clean_price
from .models import ScraperEngine

logger = get_task_logger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def check_price(self, engine_id):
    engine = None
    try:
        engine = ScraperEngine.objects.get(id=engine_id)
        products = Product.objects.filter(engine=engine)

        for product in products:
            try:
                scraper = Scraper(product.url).scrape_product()
                print(f"hasil scrape: {scraper}")
            except Exception as e:
                logger.warning(f"Failed to scrape price for {product.name}: {e}")
                continue
 
            new_price_raw = scraper.get("discount_price")
            new_price = clean_price(new_price_raw)
            print(f"New price: {new_price}")
            
            if new_price < product.last_price:
                body_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
                    <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                    <h2 style="color: #2c3e50;">🔥 Price Drop Alert!</h2>
                    <p>Hello, <strong>{product.email}</strong>,</p>

                    <p>Good news! The product you're tracking just dropped in price:</p>

                    <h3 style="margin: 10px 0;">{product.name}</h3>

                    <p>
                        <strong>Previous Price:</strong> <span style="text-decoration: line-through; color: #888;">{product.last_price}</span><br>
                        <strong>Current Price:</strong> <span style="color: #27ae60; font-weight: bold;">{new_price}</span>
                    </p>

                    <p style="margin: 20px 0;">
                        <a href="{product.url}" style="background-color: #2980b9; color: #fff; padding: 12px 20px; border-radius: 5px; text-decoration: none;">
                        View Product 🔎
                        </a>
                    </p>

                    <hr style="margin-top: 30px;">
                    <p style="font-size: 12px; color: #888;">
                        You're receiving this email because you subscribed to price alerts.
                        <br>If this wasn't you, please ignore this message.
                    </p>
                    </div>
                </body>
                </html>
                """

                try:
                    send_mail(
                        f"Price Drop Alert!!!",
                        "",
                        None,
                        [product.email],
                        fail_silently=False,
                        html_message=body_html
                    )
                    logger.info(f"Email successfully sent to {product.email}")
                except Exception as e:
                    logger.error(f"Failed to send email to {product.email}: {e}")
                    raise self.retry(exc=e)
        
                # save new price to database
                PriceHistory.objects.create(product=product, price=new_price)
                product.last_price = new_price
                product.save()

            else:
                logger.info(f"Price for {product.name} has not dropped. Current price: {new_price}, Last price: {product.last_price}")

    finally:
        if engine is not None:
            engine.task_count = max(engine.task_count - 1, 0)
            engine.save(update_fields=['task_count', 'updated_at'])


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def check_price_all_engines(*args, **kwargs):
    logger.info("Running check_price_all_engines task from beat")
    for engine in ScraperEngine.objects.all():
        check_price.delay(engine.id)

# @shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
# def initial_scrape(self, product_id):
#     try:
#         product = Product.objects.get(id=product_id)
#     except Product.DoesNotExist:
#         logger.error(f"Product with ID {product_id} does not exist")
#         return
    
#     try:
#         scraped = Scraper(product.url).scrape_product()
#         print(f"Price: {scraped['discount_price']}")
#         if not scraped:
#             logger.warning(f"Scraper failed. Product not found at {product.url}")
#             return
#     except Exception as e:
#         product.engine.task_count = max(product.engine.task_count - 1, 0)
#         product.engine.save(update_fields=['task_count'])
#         logger.error(f"Scraper failed for {product.url}: {e}")
#         raise self.retry(exc=e)
    
#     new_price = clean_price(scraped['discount_price'])
#     product.name = scraped['product_name']
#     product.last_price = new_price
#     logger.warning(f"Price: {new_price}")
#     logger.warning(f"Last price: {product.last_price}")
#     product.save(update_fields=['name', 'last_price'])

#     PriceHistory.objects.create(product=product, price=new_price)

#     logger.info(f"Initial scrape completed for: {product.name}")