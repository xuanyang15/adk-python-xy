# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any

from adk_repo_answering_agent.settings import GITHUB_BASE_URL
from adk_repo_answering_agent.settings import IS_INTERACTIVE
from adk_repo_answering_agent.settings import OWNER
from adk_repo_answering_agent.settings import REPO
from adk_repo_answering_agent.settings import VERTEXAI_DATASTORE_ID
from adk_repo_answering_agent.utils import error_response
from adk_repo_answering_agent.utils import get_request
from adk_repo_answering_agent.utils import post_request
from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool
import requests

if IS_INTERACTIVE:
  APPROVAL_INSTRUCTION = (
      "Ask for user approval or confirmation for adding the comment."
  )
else:
  APPROVAL_INSTRUCTION = (
      "**Do not** wait or ask for user approval or confirmation for adding the"
      " comment."
  )


def get_issue(issue_number: int) -> dict[str, Any]:
  """Get the details of the specified issue number.

  Args:
    issue_number: issue number of the Github issue.

  Returns:
    The status of this request, with the issue details when successful.
  """
  print(f"Attempting to get issue #{issue_number}")
  url = f"{GITHUB_BASE_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}"
  try:
    response = get_request(url)
  except requests.exceptions.RequestException as e:
    return error_response(f"{e}")
  return {"status": "success", "issue": response}


def add_comment_to_issue(issue_number: int, comment: str) -> dict[str, any]:
  """Add the specified comment to the given issue number.

  Args:
    issue_number: issue number of the Github issue
    comment: comment to add

  Returns:
    The status of this request, with the applied comment when successful.
  """
  print(f"Attempting to add comment '{comment}' to issue #{issue_number}")
  url = f"{GITHUB_BASE_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments"
  payload = {"body": comment}

  try:
    response = post_request(url, payload)
  except requests.exceptions.RequestException as e:
    return error_response(f"{e}")
  return {
      "status": "success",
      "added_comment": response,
  }


def list_comments_on_issue(issue_number: int) -> dict[str, any]:
  """List all comments on the given issue number.

  Args:
    issue_number: issue number of the Github issue

  Returns:
    The status of this request, with the list of comments when successful.
  """
  print(f"Attempting to list comments on issue #{issue_number}")
  url = f"{GITHUB_BASE_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments"

  try:
    response = get_request(url)
  except requests.exceptions.RequestException as e:
    return error_response(f"{e}")
  return {"status": "success", "comments": response}


root_agent = Agent(
    model="gemini-2.5-pro",
    name="adk_answering_agent",
    description="Answer questions about ADK repo.",
    instruction=f"""
    You are a helpful assistant that responds to questions from the GitHub repository `{OWNER}/{REPO}`
    based on information about Google ADK found in the document store: {VERTEXAI_DATASTORE_ID}.

    When user specifies a issue number, here are the steps:
    1. Use the `get_issue` tool to get the details of the issue.
      * If the issue is closed, do not respond.
    2. Use the `list_comments_on_issue` tool to list all comments on the issue.
    3. Focus on the latest comment but referece all comments if needed to understand the context.
      * If there is no comment at all, just focus on the issue title and body.
    4. If all the following conditions are met, try toadd a comment to the issue, otherwise, do not respond:
      * The latest comment is from the issue reporter.
      * The latest comment is not from you or other agents (marked as "Response from XXX Agent").
      * The latest comment is asking a question or requesting information.
      * The issue is not about a feature request.
    5. Use the `VertexAiSearchTool` to find relevant information before answering.

    IMPORTANT:
      * {APPROVAL_INSTRUCTION}
      * If you can't find the answer or information in the document store, **do not** respond.
      * Include a bolded note (e.g. "Response from ADK Answering Agent") in your comment
        to indicate this comment was added by an ADK Answering Agent.
      * Do not respond to any other issue except the one specified by the user.
      * Please include your justification for your decision in your output
        to the user who is telling with you.
      * If you uses citation from the document store, please provide a footnote
        referencing the source document format it as: "[1] URL of the document".
        * Replace the "gs://prefix/" part, e.g. "gs://adk-qa-bucket/", to be "https://github.com/google/"
        * Add "blob/main/" after the repo name, e.g. "adk-python", "adk-docs", for example:
          * If the original URL is "gs://adk-qa-bucket/adk-python/src/google/adk/version.py",
            then the citation URL is "https://github.com/google/adk-python/blob/main/src/google/adk/version.py",
          * If the original URL is "gs://adk-qa-bucket/adk-docs/docs/index.md",
            then the citation URL is "https://github.com/google/adk-docs/blob/main/docs/index.md"
        * If the file is a html file, replace the ".html" to be ".md"
    """,
    tools=[
        VertexAiSearchTool(data_store_id=VERTEXAI_DATASTORE_ID),
        get_issue,
        add_comment_to_issue,
        list_comments_on_issue,
    ],
)
