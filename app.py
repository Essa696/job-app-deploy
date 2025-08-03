import os
from flask import Flask, request, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
import pyodbc
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")

# Azure storage setup
AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER")

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)

# SQL database setup
server = os.environ.get("SQL_SERVER")
database = os.environ.get("SQL_DATABASE")
username = os.environ.get("SQL_USERNAME")
password = os.environ.get("SQL_PASSWORD")

conn_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            file = request.files['resume']

            if file.filename == '':
                flash("Please upload a resume.", "danger")
                return redirect(url_for('index'))

            filename = secure_filename(file.filename)
            blob_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(file)

            conn = pyodbc.connect(conn_string)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Applications (name, email, phone, resume_url) VALUES (?, ?, ?, ?)",
                           name, email, phone, blob_name)
            conn.commit()
            conn.close()

            flash("Application submitted successfully!", "success")
            return redirect(url_for('index'))

        except Exception as e:
            print(f"Error: {e}")
            flash("There was an error. Please try again later.", "danger")
            return redirect(url_for('index'))

    return render_template("form.html")

if __name__ == '__main__':
    app.run(debug=True)