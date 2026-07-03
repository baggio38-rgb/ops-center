import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account


@st.cache_resource(show_spinner=False)
def get_bq_client():
    if "gcp_service_account" in st.secrets:
        credentials = service_account.Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"])
        )
        return bigquery.Client(
            project=credentials.project_id,
            credentials=credentials,
        )

    return bigquery.Client()


@st.cache_data(ttl=600, show_spinner=False)
def query_bq(sql: str):
    client = get_bq_client()
    return client.query(sql).to_dataframe()