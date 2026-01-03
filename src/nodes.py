from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.state import GraphState
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from src.github_client import get_file_content
import json
from src.rag import get_retriever
from src.config import DRY_RUN, GROQ_API_KEY
from src.github_client import post_comment

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY, temperature=0.2)

# --- Node 1: Analyze Diff ---
def analyze_diff(state: GraphState):
    print("--- Analyzing Diff ---")
    prompt = ChatPromptTemplate.from_template(
        """You are a Senior Tech Lead. Summarize the technical changes in this diff.
        Focus on architectural patterns, database usage, and logging.
        
        Diff:
        {diff}
        
        Summary:"""
    )
    chain = prompt | llm | StrOutputParser()
    summary = chain.invoke({"diff": state["diff_content"]})
    return {"diff_summary": summary}

# --- Node 2: Retrieve Guidelines ---
def retrieve_guidelines(state: GraphState):
    print("--- Retrieving ADRs ---")
    retriever = get_retriever()
    # Handle empty summary case
    query = state["diff_summary"] if state["diff_summary"] else "General Code Quality"
    docs = retriever.invoke(query)
    adr_texts = [doc.page_content for doc in docs]
    return {"relevant_adrs": adr_texts}

# --- TOOL DEFINITION ---
@tool
def fetch_full_file(file_path: str, repo_name: str, commit_sha: str):
    """
    Fetches the full content of a file from the repository.
    """
    print(f"🕵️ AGENT IS FETCHING FILE: {file_path}")
    
    # Mock Response for Testing
    if repo_name == "test/repo":
        return """
        # MOCK FILE CONTENT for src/payment_processor.py
        import startuputils
        
        # This wrapper satisfies ADR-002
        log = startuputils.SecureLogger() 
        
        def process_payment(amount):
             # The diff showed a call to log.record, which matches this object
             log.record(f"Charging {amount}")
             return True
        """
    
    # Real GitHub Call
    return get_file_content(repo_name, file_path, commit_sha)

# --- Node 3: Reviewer Agent (FIXED) ---
def reviewer_agent(state: GraphState):
    print("--- Running Architecture Review ---")
    
    # 1. Check if this is a reply to a conversation
    history = state.get("conversation_history", [])
    
    # If we have history, we are in "Chat Mode"
    if history:
        print("--- 🗣️ DETECTED CONVERSATION HISTORY. SWITCHING TO CHAT MODE. ---")
        
        # Format history for LLM
        history_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])
        
        prompt = f"""
        You are the Shadow Code Reviewer. You previously reviewed code and the user has replied.
        
        Conversation History:
        {history_text}
        
        Your Goal:
        1. Answer the user's question or feedback.
        2. If the user says "This is a test file" or explains why the violation is invalid, ACCEPT it and say "Understood, flagging as resolved."
        3. Be polite but professional.
        
        Reply:
        """
        
        # We skip tool usage in Chat Mode for simplicity (or you can add it back if needed)
        response = llm.invoke(prompt)
        return {"initial_critique": response.content}

    # 2. Standard Review Mode (The code you already have)
    print("--- 🔍 NO HISTORY. RUNNING FRESH REVIEW. ---")
    
    llm_with_tools = llm.bind_tools([fetch_full_file])
    
    # ... (Keep your existing Prompt and Tool Logic here) ...
    # ... (Paste your previous reviewer_agent logic below) ...
    
    cached_content = ""
    if state.get("file_content_cache"):
        cached_content = "\n\n=== PREVIOUSLY FETCHED FILES ===\n"
        for path, content in state["file_content_cache"].items():
            cached_content += f"--- START OF {path} ---\n{content}\n--- END OF {path} ---\n"
            
    prompt_text = f"""
    You are a Strict Code Reviewer. Check the code changes against the provided ADRs.
    
    ADRs:
    {json.dumps(state['relevant_adrs'])}
    
    Diff:
    {state['diff_content']}
    
    {cached_content}
    
    RULES:
    1. If you see a violation but lack context, call `fetch_full_file`.
    2. IMPORTANT: If the file is listed in "PREVIOUSLY FETCHED FILES", DO NOT fetch it again.
    """
    
    messages = [HumanMessage(content=prompt_text)]
    response = llm_with_tools.invoke(messages)
    
    # Tool Guardrail (Keep your existing guardrail logic)
    if response.tool_calls:
        existing_files = state.get("file_content_cache", {})
        valid_calls = [c for c in response.tool_calls if c["args"].get("file_path") not in existing_files]
        if not valid_calls:
             return {"initial_critique": "I have fetched all files. Proceeding with review."}
        response.tool_calls = valid_calls
        return {"initial_critique": response}
    
    return {"initial_critique": response.content}

# --- Node 4: Tool Executor ---
def tool_executor(state: GraphState):
    print("--- Executing Tools ---")
    message = state["initial_critique"]
    new_files = {}
    
    # If the previous node returned a string (guardrail triggered), skip execution
    if isinstance(message, str):
         return {"file_content_cache": state.get("file_content_cache", {})}

    for tool_call in message.tool_calls:
        if tool_call["name"] == "fetch_full_file":
            args = tool_call["args"]
            path = args["file_path"]
            
            # Execute
            try:
                content = fetch_full_file.invoke(args)
            except Exception as e:
                content = f"Error fetching file: {e}"
                
            new_files[path] = content
            
    # Update cache (merge with existing)
    current_cache = state.get("file_content_cache", {}).copy()
    current_cache.update(new_files)
    
    return {"file_content_cache": current_cache}

# --- Node 5: Senior Filter ---
def senior_filter_agent(state: GraphState):
    print("--- Filtering Review ---")
    critique = state["initial_critique"]
    
    # Extract text content if it's an object
    if isinstance(critique, AIMessage):
        critique = critique.content
        
    prompt = ChatPromptTemplate.from_template(
        """You are a Principal Engineer. Review the initial critique.
        
        Initial Critique:
        {critique}
        
        If the critique says "No violations" or "Compliant", reply with exactly "LGTM".
        Otherwise, format the feedback nicely for GitHub.
        
        Final Comment:"""
    )
    chain = prompt | llm | StrOutputParser()
    final_comment = chain.invoke({"critique": critique})
    return {"final_comment": final_comment}

# --- Node 6: Publisher ---
def publisher_node(state: GraphState):
    comment = state["final_comment"]
    if comment.strip() == "LGTM":
        print("--- Code looks good. ---")
        return
    
    print(f"--- Posting Comment (DRY_RUN={DRY_RUN}) ---")
    print(f"Content:\n{comment}")
    
    if not DRY_RUN:
        post_comment(state["repo_name"], state["pr_number"], comment)