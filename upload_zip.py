import os
import dropbox
import shutil
import requests
from datetime import datetime

def upload_to_dropbox():
    # https://peterbanigo.com/how-to-get-a-long-lived-access-token-refresh-token-for-dropbox/
    APP_KEY = os.getenv("DROPBOX_APP_KEY")
    APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
    REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
        "client_id": APP_KEY,
        "client_secret": APP_SECRET
    }
    response = requests.post(url, data=data)

    ACCESS_TOKEN = response.json().get('access_token')

    report_id = datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    CAMINHO_DROPBOX = f'/ResultadosTestes/resultado{report_id}.zip'  # pode ser com subpasta: '/pasta/arquivo.zip'
    filename = "files"
    file_ext = "zip"
    reports_path = f"arquivos/"
    shutil.make_archive(filename, file_ext, reports_path)

    #Conectar com API
    dbx = dropbox.Dropbox(ACCESS_TOKEN)

    # Upload
    with open(f"./{filename}.{file_ext}", 'rb') as f:
        dbx.files_upload(f.read(), CAMINHO_DROPBOX, mode=dropbox.files.WriteMode.overwrite)

    # Criar link compartilhável
    link_publico = dbx.sharing_create_shared_link_with_settings(CAMINHO_DROPBOX).url
    print("Link público:", link_publico)

    # Link direto pra download
    link_download = link_publico.replace('?dl=0', '?dl=1')
    print("Link de download direto:", link_download)
    return [link_publico, link_download], report_id

upload_to_dropbox()
