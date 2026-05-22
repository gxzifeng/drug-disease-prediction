import asyncio
from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.experiment import ExperimentService

@celery_app.task(bind=True)
def run_experiment_training(self, experiment_id: int):
    async def _run():
        async with AsyncSessionLocal() as db:
            experiment_service = ExperimentService(db)
            # We need to modify start_training to accept a progress callback if we want granular progress
            # For now, let's just run it.
            await experiment_service.start_training(experiment_id)
            return {"status": "completed", "experiment_id": experiment_id}
            
    return asyncio.run(_run())
