from django.db import transaction
from .models import ScraperEngine
from logging import getLogger

logger = getLogger(__name__)

class LoadBalancer:
    @staticmethod
    def get_scraper_engine():
        try:
            with transaction.atomic():
                engine = ScraperEngine.objects.select_for_update().filter(active=True).order_by('task_count').first()
                if engine:
                    engine.task_count += 1
                    engine.save(update_fields=['task_count', 'updated_at'])
                    logger.info(f'Selected scraper engine: {engine.engine_name} with {engine.task_count} tasks')
                    return engine
                else:
                    raise Exception("No active scraper engines available")
        except Exception:
            logger.exception('Error while selecting scraper engine')
            return None