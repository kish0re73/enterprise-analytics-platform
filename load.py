# Separate from the main requirements.txt on purpose: Apache Airflow has a
# large, version-pinned dependency set that can conflict with the dashboard's
# requirements and will slow down / break a lightweight Streamlit Cloud
# deploy. Install this only in an environment actually running the Airflow
# scheduler (etl/airflow_dag.py), not alongside the dashboard.
apache-airflow>=2.9
