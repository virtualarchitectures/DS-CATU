# DS-CATU

## Running in Google Colab

<a target="_blank" href="https://colab.research.google.com/github/virtualarchitectures/DS-CATU/blob/main/notebooks/colab_interface.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

This notebook prepares the Colab environment and runs the tool to download RTB determination orders.

NOTE: As of 24/11/2025 the Colab version is not working as intended and in the meantime it is recommended to run the program locally.

## Running Locally

### Installation

```
pip install -r requirements.txt

playwright install --with-deps

```
Chrome is required to run playwright

### Downloading determination orders

```
python src/download_determination_orders.py

```



