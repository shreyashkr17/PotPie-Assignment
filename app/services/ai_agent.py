import httpx
import os
import json 
import logging
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, ValidationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class APIError(Exception):
    """Custom exception for API-related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class CodeAnalysisResult(BaseModel):
    """Structured result for code analysis."""
    type: str
    line: int
    description: str

class PRAnalysisResult(BaseModel):
    """Structured result for PR analysis."""
    task_id: str
    status: str
    results: Dict[str, Union[List[Dict], Dict]]


OLLAMA_API_URL = os.getenv("LLAMA_API_URL", "http://localhost:11434/api/generate")

async def call_llama_api(prompt: str) -> str:
    request_data = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
    }
    print(f"Prompt sent to LLaMA:\n{prompt}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OLLAMA_API_URL,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=100.0  
            )
            response.raise_for_status()
            response_data = response.json()
            
            if "response" not in response_data:
                logger.warning(f"Unexpected response format: {response_data}")
                return {"category": "Unknown", "description": "Failed to parse response."}
            
            raw_response = response_data["response"]
            try:
                category, description = map(str.strip, raw_response.split(",", 1))
                return {"category": category, "description": description}
            except ValueError:
                logger.error(f"Could not split response: {raw_response}")
                return {"category": "Error", "description": "Invalid response format"}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP Status Error: {e.response.status_code}")
        logger.error(f"Response Content: {e.response.text}")
        raise APIError(f"API call failed: {e}", e.response.status_code)
    except httpx.RequestError as e:
        logger.error(f"Network error occurred: {e}")
        raise APIError(f"Network error: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise APIError(f"An error occurred: {e}")




async def get_changed_files(repo_url: str, pr_number: int, github_token: str) -> List[Dict]:
    """
    Fetch the list of files changed in a pull request.
    """
    try:
        repo_url_parts = repo_url.strip("/").split("/")
        owner = repo_url_parts[-2]
        repo = repo_url_parts[-1]
        pr_api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"

        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(pr_api_url, headers=headers)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"GitHub API error: {e.response.status_code}")
        raise APIError(f"GitHub API error: {e}", e.response.status_code)
    
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise APIError(str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error fetching changed files: {e}")
        raise APIError(f"Unexpected error: {e}")
    
    return []


async def get_file_contents(contents_url: str, github_token: str) -> str:
    """
    Fetch the contents of a file from GitHub.
    """
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3.raw",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(contents_url, headers=headers)
        response.raise_for_status()
        return response.text


def parse_patch(patch: str) -> List[Dict]:
    """
    Parse the patch to extract line changes.
    """
    try:
        lines = patch.split("\n")
        changes = []
        current_line = 0

        for line in lines:
            if line.startswith("@@"):
                parts = line.split(" ")
                if len(parts) < 3:
                    continue
                _, old_range, new_range = parts[:3]
                _, start_line = new_range.split("+")
                current_line = int(start_line.split(",")[0])
            elif line.startswith("+") and not line.startswith("+++"):
                changes.append({"line": current_line, "code": line[1:].strip()})
                current_line += 1
            elif not line.startswith("-") and not line.startswith(" "):
                current_line += 1

        return changes
    except Exception as e:
        logger.error(f"Error parsing patch: {e}")
        return []


async def analyze_code(repo_url: str, pr_number: int, github_token: str, task_id:str) -> Dict:
    """
    Analyze the code changes in a pull request.
    Args:
        repo_url (str): The GitHub repository URL.
        pr_number (int): The pull request number.
        github_token (str): The GitHub authentication token.
        task_id (str): The task ID for tracking.
    Returns:
        Dict: Analysis results including issues and summary.
    """
    try:
        if not all([repo_url, pr_number, github_token, task_id]):
            raise ValueError("Missing required parameters")
        
        changed_files = await get_changed_files(repo_url, pr_number, github_token)

        if not changed_files:
            return {
                "task_id": "N/A",
                "status": "completed",
                "results": {
                    "files": [],
                    "summary": {
                        "total_files": 0,
                        "total_issues": 0,
                        "critical_issues": 0,
                    },
                },
            }

        results = []
        total_issues = 0
        critical_issues = 0

        for file in changed_files:
            file_name = file.get("filename", "Unknown")
            patch = file.get("patch", "")
            contents_url = file.get("contents_url", "")

            if not patch or not contents_url:
                continue

            file_contents = await get_file_contents(contents_url, github_token)

            changes = parse_patch(patch)

            issues = []
            for change in changes:
                line_number = change["line"]
                code_snippet = change["code"]

                print(line_number, code_snippet)

                try:
                    prompt = (
                        f"Analyse this line of code for issues: line no: {line_number} - {code_snippet}\n"
                        f"Categorize as one of the category in one word: Improvement, Style, Bug, Best Practice."
                        f"Response should be in one word. And then write a description for this line in 7-10 words at most."
                        f"Return response like this category, description"
                    )

                    analysis = await call_llama_api(prompt)
                    print(analysis)

                    code_issue = CodeAnalysisResult(
                            type=analysis.get("category", "Unknown"),
                            line=line_number,
                            description=analysis.get("description", "No description")
                        )
                        
                    issues.append(code_issue.dict())
                    total_issues += 1
                except Exception as analysis_error:
                    logger.error(f"Error analyzing code snippet: {analysis_error}")
                    continue

            results.append({"name": file_name, "issues": issues})

        summary = {
            "total_files": len(results),
            "total_issues": total_issues,
            "critical_issues": critical_issues,
        }

        return {
            "task_id":task_id,
            "status":"completed",
            "results":{"files": results, "summary": summary}
        }

    except APIError as api_err:
        logger.error(f"API Error during code analysis: {api_err}")
        return PRAnalysisResult(
            task_id=task_id,
            status="failed",
            results={
                "files": [],
                "summary": {"total_files": 0, "total_issues": 0, "critical_issues": 0},
                "error": str(api_err)
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in code analysis: {e}")
        return PRAnalysisResult(
            task_id=task_id,
            status="failed",
            results={
                "files": [],
                "summary": {"total_files": 0, "total_issues": 0, "critical_issues": 0},
                "error": "Unexpected system error"
            }
        )
