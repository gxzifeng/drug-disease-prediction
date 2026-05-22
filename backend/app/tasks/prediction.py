import asyncio
from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.prediction import PredictionService

@celery_app.task(bind=True)
def run_batch_prediction(self, dataset_id: int, model_id: int = None, user_id: int = None):
    async def _run():
        async with AsyncSessionLocal() as db:
            prediction_service = PredictionService(db)
            return await prediction_service.predict_batch(
                self.update_state,
                dataset_id,
                model_id,
                self.request.id
            )
            
    return asyncio.run(_run())
