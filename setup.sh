#!/bin/bash

# Define the name of your Conda environment
ENV_NAME="DS-CATU"
PYTHON_VERSION="3.8"

# Function to handle errors
error_exit()
{
    echo "Error: $1"
    exit 1
}

# Create project folders if they don't exist
echo "Creating project folders..."
mkdir -p data/downloaded_pdfs
mkdir -p data/converted_text
mkdir -p data/summary
mkdir -p reference
mkdir -p chromedriver

# Initialise existing Conda installation if not already initialised
eval "$(conda shell.bash hook)"

# Install Miniconda if not installed
if ! command -v conda &> /dev/null; then
    echo "Installing Miniconda..."
    # Make directory for Miniconda installation
    mkdir -p ~/miniconda3 || error_exit "Failed to create Miniconda directory"
    # Download Miniconda installer
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh || error_exit "Failed to download Miniconda installer"
    # Run Miniconda installer
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 || error_exit "Failed to install Miniconda"
    # Remove Miniconda installer
    rm -rf ~/miniconda3/miniconda.sh || error_exit "Failed to remove Miniconda installer"
    echo "Miniconda installed successfully and initialized"
    # Initialise Miniconda
    ~/miniconda3/bin/conda init bash
else
    echo "Miniconda is already installed"
fi

# Create new Conda environment
echo "Creating Conda environment '$ENV_NAME' with Python $PYTHON_VERSION..."
conda create -y -n $ENV_NAME python=$PYTHON_VERSION || error_exit "Failed to create Conda environment"
echo "Conda environment '$ENV_NAME' created successfully."

# Activate Conda environment
echo "Activating Conda environment '$ENV_NAME'..."
conda activate $ENV_NAME || error_exit "Failed to activate Conda environment"

# Add Conda Forge as a channel if not added already
conda config --add channels conda-forge

# Install specific version of Poppler
echo "Installing Poppler PDF utility..."
conda install -y -c conda-forge poppler || error_exit "Failed to install Poppler"

# Install Tesseract OCR binaries if not already installed
if ! command -v tesseract &> /dev/null; then
    echo "Installing Tesseract OCR binaries..."
    sudo apt-get update || error_exit "Failed to update apt repositories"
    sudo apt-get install -y tesseract-ocr libtesseract-dev || error_exit "Failed to install Tesseract OCR"
fi

# Install Chromedriver
echo "Installing Chromedriver..."
# Install the unzip utility
sudo apt-get install unzip &&
# Store the machine architecture in a variable
a=$(uname -m) &&\
# Lookup the latest release version number of Chromedriver
wget -O chromedriver/LATEST_RELEASE.txt http://chromedriver.storage.googleapis.com/LATEST_RELEASE &&
# Determine the appropriate version (32-bit or 64-bit) based on machine architecture
if [ $a == i686 ]; then 
    b=32 
elif [ $a == x86_64 ]; then 
    b=64 
fi &&
latest=$(cat chromedriver/LATEST_RELEASE.txt) &&
# Download the latest version of Chromedriver based on the architecture
wget -O chromedriver/chromedriver.zip 'http://chromedriver.storage.googleapis.com/'$latest'/chromedriver_linux'$b'.zip' &&
# Unzip the downloaded Chromedriver into the 'chromedriver' directory
unzip chromedriver/chromedriver.zip -d chromedriver/ || error_exit "Failed to unzip Chomedriver.zip" &&
rm -rf chromedriver/chromedriver.zip || error_exit "Failed to remove Chomedriver.zip" &&
rm -rf chromedriver/LATEST_RELEASE.txt || error_exit "Failed to remove LATEST_RELEASE.txt" &&
echo "Chromedriver successfully installed!"

# Install requirements
if [ -f requirements.txt ]; then
    echo "Installing Python requirements..."
    pip install -r requirements.txt || error_exit "Failed to install Python requirements"
    echo "Requirements installed successfully."
else
    echo "No requirements.txt file found."
fi

# Deactivate the virtual environment
conda deactivate

echo "Conda environment '$ENV_NAME' created and requirements installed."
