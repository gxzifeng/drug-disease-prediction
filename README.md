#  Drug-Disease Association Prediction Platform

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95-009688.svg)
![Vue3](https://img.shields.io/badge/Vue.js-3.0-4FC08D.svg)
![Celery](https://img.shields.io/badge/Celery-Distributed_Task-37814A.svg)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)

A high-performance, full-stack prototype system designed to predict potential drug repurposing targets (Drug-Disease Associations) using network representation learning and tree-based ensemble models. 

This project demonstrates the integration of complex biomedical data processing with a modern, asynchronous Web architecture, ensuring high throughput and non-blocking user experiences.

##  Core Features & Architecture

- **Asynchronous Task Scheduling**: Integrated **Celery** and **Redis** to decouple computationally intensive machine learning tasks (e.g., Graph Neural Network training) from the main Web threads. Achieved a peak throughput of 210 TPS with a stable TP99 response time of 680ms under concurrent testing.
- **Dual-Stage Algorithmic Framework**: 
  - *Representation Learning*: Employs **Node2Vec** and 2-layer **GCN** (Graph Convolutional Networks) to extract topological features from bipartite networks.
  - *Classification*: Utilizes an **XGBoost** classifier to compute reliable target correlation probabilities (achieving an AUC score of 0.893 on simulated datasets).
- **Automated Data Pipeline**: Built an end-to-end pipeline processing raw CSV/TSV biomedical datasets into structured MySQL relational databases, fully mapped and cleaned for ML model ingestion.
- **Interactive Visualization**: Features a dynamic dashboard built with **Vue3**, **TypeScript**, and **ECharts** for real-time bipartite network topology mapping and prediction result tracking.
- **Enterprise-Grade Security**: Implemented strict Role-Based Access Control (RBAC) via JWT double-token authentication mechanisms.

## Technology Stack

- **Backend / API**: Python 3.10, FastAPI, SQLAlchemy ORM
- **Task Queue / Cache**: Celery, Redis 7
- **Database**: MySQL 8.0 (InnoDB)
- **Machine Learning**: PyTorch, NetworkX, Scikit-learn, XGBoost
- **Frontend**: Vue 3, Element Plus, ECharts

## Deployment (Dockerized)

This application is fully containerized for seamless cross-platform deployment. To spin up the entire stack (Database, Cache, Backend API, Celery Workers, and Frontend), simply run:

```bash
docker-compose up --build -d