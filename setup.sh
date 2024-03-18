#!/bin/bash

# Initialize Conda if not already initialized
eval "$(conda shell.bash hook)"

# Define the name of your Conda environment
ENV_NAME="DS-CATU"

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
