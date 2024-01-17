import os

import openai

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger.addHandler(handler)


openai.api_type = 'azure'
openai.api_key = 'b59f23e204b3426c9dbe1f6741b80acb'
openai.api_version = "2022-12-01"
openai.azure_endpoint='https://trail-outcome.openai.azure.com/'
 
# os.environ["OPENAI_API_TYPE"] = "azure"
# os.environ["OPENAI_API_VERSION"] = "2022-12-01"
# os.environ["OPENAI_API_BASE"] = "https://trail-outcome.openai.azure.com/"
# os.environ["OPENAI_API_KEY"] = "b59f23e204b3426c9dbe1f6741b80acb"
 
import requests
import re
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI()

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/")
async def read_root(data: dict):
    # return {"message": "Hello, World!"}
    
    
    def fetch_github_files_recursive(github_link, file_regex=None):
        # Extract owner, repo, and branch from the GitHub link
        # Example link: https://github.com/owner/repo/tree/branch
        parts = github_link.rstrip('/').split('/')
        owner, repo, _, branch = parts[-4:]
    
        # GitHub API URL for fetching repository contents
        api_url = f'https://api.github.com/repos/{owner}/{repo}/contents'
    
        # Recursive function to fetch files from all folders
        def fetch_files_recursive(folder_path=''):
            response = requests.get(f'{api_url}/{folder_path}', params={'ref': branch})
        
            if response.status_code == 200:
                files = response.json()
                fetched_files = []
    
                for file in files:
                    # If it's a directory, recursively fetch files from it
                    if file['type'] == 'dir':
                        fetched_files.extend(fetch_files_recursive(file['path']))
                    else:
                        # Check if the file matches the provided regex pattern
                        if file_regex and re.match(file_regex, file['name']):
                            #continue
    
                            # Fetch file content
                            content_response = requests.get(file['download_url'])
                            if content_response.status_code == 200:
                                fetched_files.append({
                                
                                    'name': file['name'],
                                    'content': content_response.text
                                })
                            time.sleep(1)
    
                return fetched_files
    
            else:
                # print(f"URL: {response.url}")
                # print(f"Response Content: {response.text}")
                print(f"Failed to fetch GitHub files. Status code: {response.status_code}")
                return []
    
        # Start recursive fetching from the root folder
        return fetch_files_recursive()

    def print_files(files):
        print(type(files))
        if files:
            for file in files:
                print(f"File Name: {file['name']}")
                print(f"File Content:\n{file['content']}\n{'=' * 40}")

    def generate_documentation(prompt, code_snippets):
        prompt += code_snippets

        # Adjust the temperature and max tokens according to your preference
        response = openai.completions.create(
            model="LMM_OPENAI",
            prompt=prompt,
            temperature=0,
            max_tokens=1000,
            # n=1,
            # stop=None
        )

        return response.choices[0].text

    def main():
        # Parsing Github files:
        logger.info(f"In main")
        print("in main")
        link = data.get('data')
        github_link = link +"/tree/main"
        logger.info("Github link", github_link)

     
        file_regex = r'.*\.py'  # Specify a regex pattern if needed
        files = fetch_github_files_recursive(github_link, file_regex)

        # print_files(files)

        documents = ""
        for file in files:
            prompt = """Generate a documentation of given code in short using bullet points,
                        things to do-
                        1. give comments on important lines of code and rewrite the whole code
                        2. write sample input and output of code
                        3. finally give a one line summary of code
                        DON'T INCLUDE RELATED POST IN OUTPUT\n\n"""
            code_snippets = file['content']
            generated_text = generate_documentation(prompt, code_snippets)
            # print(generated_text)
            temp = "\n\n" + generated_text
            documents += f"""\n ************************************** \n\n
                            FILE NAME--------- {file['name']} \n  {temp} """
        logger.info(documents)
        # file_name1 = "output1.txt"
        with open('/home/site/wwwroot/myfile.txt', 'w') as file:
            file.write(str(documents))
        logger.info(f"File generated")

        # return {"message": "Files generated successfully"}
    main()
