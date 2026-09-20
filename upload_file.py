import os

def upload_file(client, path):

    if not os.path.exists(path):
        raise FileNotFoundError(path)

    print("Uploading PDF...")

    uploaded_file = client.files.upload(file=path)

    print("Upload successful.")

    return uploaded_file