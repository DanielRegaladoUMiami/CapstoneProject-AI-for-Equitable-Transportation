# 🚍 AI for Equitable Public Transportation

> Predicting transit access gaps and equity issues across Miami's diverse communities using AI-driven demand forecasting and simulation.

[![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)]()
[![Python](https://img.shields.io/badge/Python-3.10+-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

## 📋 Problem Statement

A Miami-based transit authority needs a model that predicts public transportation access gaps and emerging equity issues across their service area. The region features diverse demographics and a mix of densely populated urban centers and underserved outlying communities. Residents need up-to-date insights about their access to reliable, affordable, and efficient transit options — especially as neighborhoods change, new developments arise, or service changes occur.

**Industry Focus:** Demand Forecasting · Universal Service Design · Accessibility

## 🎯 Project Goals

### Level 1 — Data Analysis & Predictive Modeling
- Clean and analyze demographic/socioeconomic data, transit usage/operations data, and community feedback
- Build regression and time series models to predict future transit demand and identify where service gaps and inequities are likely to occur

### Level 2 — Simulation
- Design an AI model that simulates the impact of proposed service changes (e.g., wait times, equity outcomes)

### Level 3 — Dashboard
- Build an interactive dashboard to visualize local transit access, ridership analytics, alerts, and recommendations

## 📦 Expected Deliverables

| Deliverable | Description |
|---|---|
| **Exploratory Data Analysis** | Statistical profiling and visualization of transit and demographic data |
| **Prediction Model** | Regression & time series models for demand forecasting and gap identification |
| **Simulation Model** | Impact simulation for proposed service changes |
| **Interactive Dashboard** | Visual interface for transit access, ridership, and equity insights |

## 📊 Data Sources

| Dataset | Source | Description |
|---|---|---|
| **Demographic Data** | [US Census Bureau (ACS 2023)](https://data.census.gov/table/ACSDP1Y2023.DP03?q=DP03&g=040XX00US12) | Socioeconomic and demographic profiles for Florida |
| **Transit System Data** | [General Transit Feed Specification (GTFS)](https://gtfs.org/) | Schedule and real-time transit data |
| **Accessibility Data** | [National Accessibility Evaluation](https://www.arcgis.com/home/item.html?id=40526f1e2c734241bab4d3bb41385c51) | Transit accessibility metrics |

## 🛠️ Tech Stack

- **Languages:** Python
- **Analysis:** Pandas, NumPy, Scikit-learn, Statsmodels
- **Visualization:** Plotly, Matplotlib, Seaborn
- **Dashboard:** Streamlit / Dash *(TBD)*
- **Data:** GTFS, Census API, ArcGIS

## 🚀 Getting Started

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/CapstoneProject-AI-for-Equitable-Transportation.git
cd CapstoneProject-AI-for-Equitable-Transportation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 📁 Project Structure

```
├── data/               # Raw and processed datasets
├── notebooks/          # Jupyter notebooks for EDA and modeling
├── src/                # Source code for models and pipeline
├── dashboard/          # Dashboard application
├── reports/            # Generated analysis reports
├── requirements.txt    # Python dependencies
└── README.md
```

## 👥 Team

- **Gabby Ridge** — Project Lead & Content Creator

---

*Capstone Project — University of Miami, MS in Business Analytics*
