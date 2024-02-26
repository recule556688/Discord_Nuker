#!/bin/bash

# Define the service name
SERVICE_NAME="discord-bot-nuker"

# Function to pull the latest Docker image
pull_image() {
    echo "Pulling latest Docker image from the registry..."
    if docker-compose pull $SERVICE_NAME; then
        echo "Successfully pulled latest Docker image."
    else
        echo "Failed to pull latest Docker image."
        exit 1
    fi
}

# Function to stop and remove the running Docker container
remove_container() {
    echo "Stopping and removing the running Docker container..."
    if docker-compose down; then
        echo "Successfully stopped and removed the Docker container."
    else
        echo "Failed to stop and remove the Docker container."
        exit 1
    fi
}

# Function to run the latest Docker image
run_image() {
    echo "Running latest Docker image..."
    if docker-compose up -d $SERVICE_NAME; then
        echo "Successfully started new Docker container."
    else
        echo "Failed to start new Docker container."
        exit 1
    fi
}

# Main script execution
echo "Starting update script..."
pull_image
remove_container
run_image
echo "Update script finished."