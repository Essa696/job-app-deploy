import os
from flask import Flask, request, render_template, redirect, url_for
from azure.storage.blob import BlobServiceClient
import pyodbc
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)

# -----------------------------
# ENVIRONMENT VARIABLES (use Azure App Settings in production)
# -----------------------------
AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER")
SQL_SERVER = os.environ.get("SQL_SERVER")
SQL_DATABASE = os.environ.get("SQL_DATABASE")
SQL_USERNAME = os.environ.get("SQL_USERNAME")
SQL_PASSWORD = os.environ.get("SQL_PASSWORD")

# -----------------------------
# DB Connection
# -----------------------------
def get_db_connection():
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={SQL_SERVER};'
        f'DATABASE={SQL_DATABASE};'
        f'UID={SQL_USERNAME};'
        f'PWD={SQL_PASSWORD}'
    )
    return pyodbc.connect(conn_str)

# -----------------------------
# Azure Blob Upload
# -----------------------------
def upload_resume_to_blob(file):
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)

    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(file, overwrite=True)
    return blob_client.url

# -----------------------------
# Routes
# -----------------------------
@app.route('/', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        position = request.form['position']
        resume = request.files['resume']

        if resume:
            resume_url = upload_resume_to_blob(resume)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Applications (Name, Email, Position, ResumeUrl) VALUES (?, ?, ?, ?)",
                (name, email, position, resume_url)
            )
            conn.commit()
            conn.close()

            return "Application submitted successfully!"

    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)