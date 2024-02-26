#!/bin/bash

# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Prompt for the service name
read -p "Enter the name of the service (default: discord-bot-nuker): " SERVICE_NAME
SERVICE_NAME=${SERVICE_NAME:-discord-bot-nuker}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Docker does not seem to be running, start it first and rerun the script${NC}"
        exit 1
    fi
}

# Function to stop the Docker container if it's already running
stop_container() {
    if [ "$(docker ps -q -f name=$SERVICE_NAME)" ]; then
        echo -e "${GREEN}Container is already running, updating it...${NC}"
        echo -e "${GREEN}Stopping existing Docker container...${NC}"
        if docker-compose down $SERVICE_NAME; then
            echo -e "${GREEN}Successfully stopped Docker container.${NC}"
        else
            echo -e "${RED}Failed to stop Docker container.${NC}"
            exit 1
        fi
    fi
}

# Function to pull the Docker image
pull_image() {
    echo -e "${GREEN}Pulling Docker image from the registry...${NC}"
    if docker-compose pull $SERVICE_NAME; then
        echo -e "${GREEN}Successfully pulled Docker image.${NC}"
    else
        echo -e "${RED}Failed to pull Docker image.${NC}"
        exit 1
    fi
}

# Function to run the Docker image
run_image() {
    echo -e "${GREEN}Running Docker image...${NC}"
    if docker-compose up -d --no-deps $SERVICE_NAME; then
        echo -e "${GREEN}Successfully started Docker container.${NC}"
    else
        echo -e "${RED}Failed to start Docker container.${NC}"
        exit 1
    fi
}

# Function to handle script termination
handle_exit() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}An error occurred while executing the script. Please check the logs above.${NC}"
    else
        echo -e "${GREEN}Deployment script finished successfully.${NC}"
    fi
    exit $exit_code
}

# Register the function to be called on EXIT
trap handle_exit EXIT

# Main script execution
echo -e "${GREEN}Starting deployment script...${NC}"
check_docker
stop_container
pull_image
run_image
