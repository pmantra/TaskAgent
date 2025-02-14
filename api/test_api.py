import asyncio
import os

import requests
import json
import argparse
import traceback
from typing import List, Dict, Any

from dotenv import load_dotenv

load_dotenv()
BASE_URL = "http://127.0.0.1:8000/tasks"


class TaskAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def create_task(self, description: str) -> Dict[str, Any]:
        """Send a request to create a task"""
        payload = {
            "description": description
        }
        try:
            response = self.session.post(f"{self.base_url}", json=payload)

            print(f"Create Task Response: {response.status_code}")
            print(f"Response Content: {response.text}")

            if response.status_code in [200, 201]:
                task = response.json()
                print(f"✅ Task Created: {description}")

                # Debug: Check if embedding exists
                if 'embedding' in task:
                    print(f"Embedding: {task['embedding']}")
                else:
                    print("⚠️ No embedding found in task response")

                return task
            else:
                print(f"❌ Failed to create task: {description}")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"Exception in create_task: {e}")
            traceback.print_exc()
            return None

    def search_similar_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Search for similar tasks using embeddings"""
        try:
            response = self.session.get(f"{self.base_url}/search", params={"query": query})

            print(f"\n🔍 Searching Similar Tasks for '{query}'")
            print(f"Search Tasks Response: {response.status_code}")
            print(f"Response Content: {response.text}")

            if response.status_code == 200:
                similar_tasks = response.json()

                if not similar_tasks:
                    print("❗ No similar tasks found")
                else:
                    print(f"Found {len(similar_tasks)} similar tasks:")
                    for task in similar_tasks:
                        print(json.dumps(task, indent=2))

                return similar_tasks
            else:
                print(f"❌ Failed to search tasks")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return []
        except Exception as e:
            print(f"Exception in search_similar_tasks: {e}")
            traceback.print_exc()
            return []


async def main():
    parser = argparse.ArgumentParser(description="Task API Tester")
    parser.add_argument("--url", default="http://127.0.0.1:8000/tasks", help="Base URL for the API")
    args = parser.parse_args()

    # Ensure OpenAI API Key is Set
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ ERROR: OPENAI_API_KEY is not set. Please set it before running the script.")
        exit(1)

    print(f"✅ OpenAI API Key Loaded: {openai_api_key[:5]}... (truncated for security)")

    tester = TaskAPITester(args.url)

    # Test task descriptions
    task_descriptions = [
        "Prepare quarterly business presentation for marketing team with detailed analytics",
        "Conduct comprehensive performance review for software engineering team",
        "Analyze Q2 financial reports and create executive summary",
        "Develop strategic new product roadmap for cloud services platform",
        "Plan immersive team building workshop for tech department"
    ]

    # Create tasks
    # created_tasks = []
    # for description in task_descriptions:
    #     task = tester.create_task(description)
    #     if task:
    #         created_tasks.append(task)

    # More comprehensive search queries
    search_queries = [
        "marketing team presentation strategy",
        "software team performance evaluation",
        "financial analysis and reporting",
        "cloud product development roadmap",
        "technology team collaboration workshop"
    ]

    for query in search_queries:
        tester.search_similar_tasks(query)

if __name__ == "__main__":
    asyncio.run(main())

