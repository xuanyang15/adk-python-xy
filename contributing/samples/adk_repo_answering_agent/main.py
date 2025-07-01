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

import asyncio
import time

from adk_repo_answering_agent import agent
from adk_repo_answering_agent.settings import ISSUE_NUMBER
from adk_repo_answering_agent.settings import OWNER
from adk_repo_answering_agent.settings import REPO
from adk_repo_answering_agent.utils import parse_number_string
from google.adk.agents.run_config import RunConfig
from google.adk.runners import InMemoryRunner
from google.adk.runners import Runner
from google.genai import types

APP_NAME = "adk_repo_answering_app"
USER_ID = "adk_repo_answering_user"


async def call_agent_async(
    runner: Runner, user_id: str, session_id: str, prompt: str
) -> str:
  """Call the agent asynchronously with the user's prompt."""
  content = types.Content(
      role="user", parts=[types.Part.from_text(text=prompt)]
  )

  final_response_text = ""
  async for event in runner.run_async(
      user_id=user_id,
      session_id=session_id,
      new_message=content,
      run_config=RunConfig(save_input_blobs_as_artifacts=False),
  ):
    if event.content and event.content.parts:
      if text := "".join(part.text or "" for part in event.content.parts):
        print(f"** {event.author} (ADK): {text}")
        if event.author == agent.root_agent.name:
          final_response_text += text

  return final_response_text


async def main():
  runner = InMemoryRunner(
      agent=agent.root_agent,
      app_name=APP_NAME,
  )
  session = await runner.session_service.create_session(
      app_name=APP_NAME, user_id=USER_ID
  )

  issue_number = parse_number_string(ISSUE_NUMBER)
  if not issue_number:
    print(f"Error: Invalid issue number received: {ISSUE_NUMBER}.")
    return

  prompt = (
      f"Please check issue #{issue_number} see if you can help answer the"
      " question or provide some information!"
  )
  response = await call_agent_async(runner, USER_ID, session.id, prompt)
  print(f"<<<< Agent Final Output: {response}\n")


if __name__ == "__main__":
  start_time = time.time()
  print(
      f"Start Q&A checking on {OWNER}/{REPO} issue #{ISSUE_NUMBER} at"
      f" {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time))}"
  )
  print("-" * 80)
  asyncio.run(main())
  print("-" * 80)
  end_time = time.time()
  print(
      "Q&A checking finished at"
      f" {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_time))}",
  )
  print("Total script execution time:", f"{end_time - start_time:.2f} seconds")
