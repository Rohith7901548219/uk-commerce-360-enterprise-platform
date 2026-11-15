from commerce.cli import bootstrap
from commerce.ingest import download_data

if __name__ == "__main__":
    bootstrap()
    print(download_data())
