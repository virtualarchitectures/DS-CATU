#!/bin/bash

# Initialise existing Conda installation if not already initialised
eval "$(conda shell.bash hook)"

# Define the name of your Conda environment
ENV_NAME="DS-CATU"

# Check if Miniconda is already installed
if command -v conda &> /dev/null; then
    echo "Miniconda is already installed"
else
    echo "Installing Miniconda..."
    # Make directory for Miniconda installation
    mkdir -p ~/miniconda3 || error_exit "Failed to create Miniconda directory"
    # Download Miniconda installer
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh || error_exit "Failed to download Miniconda installer"
    # Run Miniconda installer
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 || error_exit "Failed to install Miniconda"
    # Remove Miniconda installer
    rm -rf ~/miniconda3/miniconda.sh || error_exit "Failed to remove Miniconda installer"
    echo "Miniconda installed successfully and initialised"
    # Initialise miniconda
    ~/miniconda3/bin/conda init bash
fi

# Create new Conda environment
echo "Creating Conda environment..."
conda create -y -n $ENV_NAME python=3.12
echo "Conda environment '$ENV_NAME' created successfully."

# Activate Conda environment
echo "Activating Conda environment 'DS-CATU'..."
conda activate $ENV_NAME

# Create project folders if they don't exist
echo "Creating project folders..."
mkdir -p data/input
mkdir -p data/output
mkdir -p reference

# Add Conda Forge as a channel if not added already
conda config --add channels conda-forge

# Install specific version of Poppler
echo "Installing Poppler PDF utility..."
conda install -y -c conda-forge poppler

# Install tesseract binaries
echo "Installing Tesseract OCR binaries..."
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev

# Install requirements
if [ -f requirements.txt ]; then
    echo "Installing Python requirements..."
    pip install -r requirements.txt
    echo "Requirements installed successfully."
else
    echo "No requirements.txt file found."
fi

# Deactivate the virtual environment
conda deactivate

echo "Conda environment '$ENV_NAME' created and requirements installed."
