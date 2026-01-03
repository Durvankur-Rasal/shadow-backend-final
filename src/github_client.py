from github import Github
from src.config import GITHUB_TOKEN

def get_pr_diff(repo_name: str, pr_number: int) -> str:
    """Fetches the diff text from a GitHub PR."""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is missing in .env")
    
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    # We get the list of files and their patches
    diff_text = ""
    for file in pr.get_files():
        diff_text += f"File: {file.filename}\n"
        diff_text += f"Changes:\n{file.patch}\n\n"
    
    return diff_text

def post_comment(repo_name: str, pr_number: int, comment: str):
    """Posts a comment to the PR."""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(comment)
    print(f"✅ Comment posted to PR #{pr_number}")
    

# src/github_client.py

def get_file_content(repo_name: str, file_path: str, ref: str = "main") -> str:
    """
    Fetches the full content of a specific file from GitHub.
    """
    if not GITHUB_TOKEN:
        return "Error: GITHUB_TOKEN missing."
        
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(repo_name)
    try:
        # Get the file content at the specific commit/branch (ref)
        file_content = repo.get_contents(file_path, ref=ref)
        return file_content.decoded_content.decode("utf-8")
    except Exception as e:
        return f"Error fetching file: {str(e)}"
   
   
    
def get_pr_comments(repo_name: str, pr_number: int):
    """
    Fetches the conversation history (comments) from a PR.
    Returns a list of dicts: [{'user': 'bot', 'body': '...'}, {'user': 'human', 'body': '...'}]
    """
    if not GITHUB_TOKEN:
        return []

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    comments = []
    
    # 1. Get Issue Comments (General conversation)
    for comment in pr.get_issue_comments():
        role = "bot" if "bot" in comment.user.type.lower() or comment.user.login == "github-actions[bot]" else "human"
        comments.append({"role": role, "content": comment.body})
        
    return comments