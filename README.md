# Code Analysis Backend

## Project Overview

This is a sophisticated backend application for automated code analysis, specifically designed to analyze GitHub Pull Requests (PRs) using AI-powered insights. The application leverages modern Python technologies to provide detailed code review assistance.

## Key Technologies
 - FastAPI: Web framework
 - Celery: Asynchronous task queue
 - Redis: Caching and task management
 - Ollama/LLaMA: AI-powered code analysis
 - Docker: Containerization

## Prerequisites
 - Docker
 - Docker Compose
 - GitHub Personal Access Token
 - Ollama (with LLaMA3 model)

## Installation and Setup

1. Clone the Repository and setup Virtual Environment
```
git clone https://github.com/shreyashkr17/PotPie-Assignment.git
cd potpie-assignment/

python3.8 -m venv venv
pip install -r requirements.txt
```

2. Environment Configuration

Create a .env file with the following configurations:

```
LLAMA_MODEL_PATH=<llama_model_running_on_localhost>
REDIS_HOST=<redis_host>
REDIS_PORT=<redis_port>
REDIS_PASSWORD=<redis_pwd>
```

3. Docker Setup

Required Modifications
- Ensure Ollama is running locally
- Ensure Redis is running locally
- Configure network settings if needed

4. Build and Run
```
# Build Docker containers
docker-compose build

# Start the services
docker-compose up
```

## Endpoints

### Trigger PR Analysis
- Endpoint: /analyze-pr
- Method: POST
- Description: Initiates code analysis for a GitHub Pull Request
- Request Body:
```
{
  "repo_url": "https://github.com/username/repository",
  "pr_number": 123,
  "github_token": "your_github_token"
}
```
- Response:
```
{
  "task_id": "unique_task_identifier"
}
```

### Check Task Status
- Endpoint: /status/{task_id}
- Method: GET
- Description: Retrieve the current status of an analysis task
- Response:
```
{
  "task_id": "unique_task_identifier",
  "status": "processing/completed/failed"
}
```

### Get Analysis Results
- Endpoint: /results/{task_id}
- Method: GET
- Description: Fetch detailed analysis results for a specific task
- Response:
```
{
  "results": {
    "files": [
      {
        "name": "filename.py",
        "issues": [
          {
            "type": "Bug/Improvement/Style",
            "line": 10,
            "description": "Detailed code issue description"
          }
        ]
      }
    ],
    "summary": {
      "total_files": 3,
      "total_issues": 5,
      "critical_issues": 2
    }
  }
}
```

## Workflow Explanation

### 1. PR Analysis Initiation
- User sends a POST request to /analyze-pr
- Backend creates a Celery task
- Returns a unique task identifier

### 2. Task Processing
- Celery worker fetches GitHub PR details
- Retrieves changed files
- Analyzes each code change using LLaMA
- Generates categorized insights

### 3. Result Retrieval
- User can check task status via /status/{task_id}
- Once completed, retrieve results via /results/{task_id}





