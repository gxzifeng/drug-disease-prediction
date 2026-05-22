"""API routes package."""
from app.api import (
    health,
    auth,
    users,
    datasets,
    drugs,
    diseases,
    graphs,
    embeddings,
    experiments,
    models,
    predictions,
)

__all__ = [
    "health",
    "auth",
    "users",
    "datasets",
    "drugs",
    "diseases",
    "graphs",
    "embeddings",
    "experiments",
    "models",
    "predictions",
]
