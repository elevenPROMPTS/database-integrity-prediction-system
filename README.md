
# Database Integrity Violation Prediction & Prevention System

## Overview
An intelligent database security system that uses Machine Learning to identify suspicious database operations and help prevent potential integrity violations.

## Problem Statement
Traditional database systems rely heavily on predefined rules to identify suspicious operations. This project introduces an ML-based anomaly detection layer to identify unusual database activities.

## Technologies Used
- Python
- FastAPI
- PostgreSQL
- Scikit-learn
- Isolation Forest
- SQL

## Key Features
- Machine Learning-based anomaly detection.
- Detection of unusual database queries.
- Rule-based blocking of potentially dangerous operations.
- Database logging of suspicious activities.
- REST API for query analysis.

## System Architecture
User Query → FastAPI Backend → Security Analysis → ML Anomaly Detection → PostgreSQL → Response

## Machine Learning
The project uses the Isolation Forest algorithm to classify database activities as normal or anomalous based on selected query-related features.

## Future Improvements
- Real-time monitoring dashboard.
- Advanced anomaly detection models.
- Improved threat analysis and reporting.

## Author
CSE (AI/ML), Veer Surendra Sai University of Technology (VSSUT), Burla.

## Project Status
Developed as an academic project.
