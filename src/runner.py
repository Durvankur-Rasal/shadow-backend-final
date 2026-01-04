import os
from github import Github
from src.graph import build_graph
from src.github_client import get_pr_diff, get_pr_comments
from src.rag import get_retriever

# Initialize DB once when the module loads (or verify it exists)
# This keeps the app "warm"
if not os.path.exists("./chroma_db"):
    print("🚀 Initializing Vector DB...")
    get_retriever("./adrs")

def run_review_task(repo_name: str, pr_number: int):
    """
    The core worker function.
    """
    print(f"▶️ Starting Review for {repo_name} PR #{pr_number}")
    
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)
    pr_obj = g.get_repo(repo_name).get_pull(pr_number)
    head_sha = pr_obj.head.sha
    
    # 1. Fetch History
    history = get_pr_comments(repo_name, pr_number)
    
    # Loop Guard
    if history and history[-1]['role'] == 'bot':
        print("🛑 Skipping: Last comment is from bot.")
        return

    # 2. Prepare Inputs
    diff_text = get_pr_diff(repo_name, pr_number)
    
    inputs = {
        "repo_name": repo_name,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "diff_content": diff_text,
        "relevant_adrs": [],
        "file_content_cache": {},
        "conversation_history": history
    }

    # 3. Run Graph
    app = build_graph()
    config = {"recursion_limit": 50}
    
    # We iterate to execute the graph, but we don't need to print every step in prod
    print("🧠 AI is thinking...")
    for _ in app.stream(inputs, config=config):
        pass # Just let it run
        
    print(f"✅ Review Complete for {repo_name} PR #{pr_number}")