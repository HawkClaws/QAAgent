import os
import sys
import argparse
import strands
from dotenv import load_dotenv
from strands import Agent
from strands.models import OpenAIModel, AnthropicModel, GeminiModel

# Import specific tools directly to avoid loading IDE-dependent ones
from serena.tools.file_tools import ListDirTool, ReadFileTool, FindFileTool, SearchForPatternTool
from serena.tools.cmd_tools import ExecuteShellCommandTool

# Load environment variables from .env
load_dotenv()

# Map provider to model config
# We keep simple map for default model names if not specified
DEFAULT_MODELS = {
    "openai": "gpt-5.2",
    "anthropic": "claude-4.5-sonnet",
    "gemini": "gemini-3.0-pro",
}

class SimpleProject:
    def __init__(self, root: str):
        self.project_root = os.path.abspath(root)

    def validate_relative_path(self, relative_path: str):
        # Basic validation to ensure path is within root
        abs_path = os.path.abspath(os.path.join(self.project_root, relative_path))
        if not abs_path.startswith(self.project_root):
            raise ValueError(f"Path outside root: {relative_path}")

    def relative_path_exists(self, relative_path: str) -> bool:
        return os.path.exists(os.path.join(self.project_root, relative_path))

    def is_ignored_path(self, path: str, ignore_non_source_files: bool = False) -> bool:
        # Simple implementation: Don't ignore anything for now to allow full exploration
        # Could add basic .git check if needed
        return ".git" in str(path).split(os.path.sep)
    
    def read_file(self, relative_path: str) -> str:
        with open(os.path.join(self.project_root, relative_path), 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

class SimpleAgent:
    def __init__(self, root: str):
        self._project = SimpleProject(root)

    def get_project_root(self) -> str:
        return self._project.project_root

    def get_active_project_or_raise(self):
        return self._project
    
    def tool_is_active(self, tool_cls) -> bool:
        return True
        
    def get_active_tool_names(self) -> list[str]:
        return ["list_dir", "read_file", "find_file", "search_for_pattern", "execute_shell_command"]

# ... imports
from serena.tools import ToolRegistry

# ... (keep SimpleProject/SimpleAgent)

def get_serena_tools():
    """Dynamically load and wrap specific Serena tools for Strands."""
    # Use current working directory as project root
    cwd = os.getcwd()
    agent_impl = SimpleAgent(cwd)

    registry = ToolRegistry()
    tools = []
    
    # helper to check if tool is safe
    def is_safe_tool(tool_cls):
        name = tool_cls.__name__
        # JetBrains tools require IDE plugin connection
        if "JetBrains" in name:
            return False
        # Skip abstract base classes if they somehow got into registry (unlikely but safe)
        if name.startswith("Tool") and name.endswith("Marker"): 
            return False
        return True

    for tool_cls in registry.get_all_tool_classes():
        if not is_safe_tool(tool_cls):
            continue

        try:
            # Instantiate tool with our SimpleAgent
            tool_instance = tool_cls(agent_impl)
            
            func = tool_instance.apply
            tool_name = tool_instance.get_name_from_cls()
            
            # Create wrapper to maintain metadata
            # Use a factory to capture tool_instance correctly in closure
            def create_wrapper(instance):
                def wrapper(*args, **kwargs):
                    return instance.apply(*args, **kwargs)
                return wrapper

            wrapper = create_wrapper(tool_instance)
            
            wrapper.__name__ = tool_name
            wrapper.__doc__ = tool_instance.apply.__doc__
            try:
                import inspect
                wrapper.__signature__ = inspect.signature(tool_instance.apply)
            except:
                pass

            final_tool = strands.tool(wrapper)
            tools.append(final_tool)
            
        except Exception as e:
            # print(f"Warning: Failed to load tool {tool_cls.__name__}: {e}")
            continue
            
    return tools

def main():
    parser = argparse.ArgumentParser(description="GitHub Repository QA Agent")
    parser.add_argument("--query", "-q", type=str, help="Question to ask the agent")
    parser.add_argument("--provider", "-p", type=str, choices=DEFAULT_MODELS.keys(), help="LLM Provider")
    parser.add_argument("--model", "-m", type=str, help="Specific model name (overrides provider default)")
    
    args = parser.parse_args()
    
    # Priority: Args > Env > Default
    provider = args.provider or os.getenv("PROVIDER", "openai")
    model_name_arg = args.model or os.getenv("MODEL_NAME")
    
    model_id = model_name_arg if model_name_arg else DEFAULT_MODELS.get(provider, "gpt-5.2")
    
    # Query might come from args or Env (for easier CI integration if needed)
    query = args.query
    if not query:
        print("Error: Query must be provided via --query argument.")
        sys.exit(1)
    
    print(f"Initializing QA Agent with model: {model_id} (Provider: {provider})")

    # Instantiate the correct Model class
    # Strands defaults to BedrockModel if a string is passed, so we MUST instantiate the correct class.
    llm_model = None
    if provider == "openai":
         if not os.getenv("OPENAI_API_KEY"):
             print("Error: OPENAI_API_KEY not found.")
             sys.exit(1)
         llm_model = OpenAIModel(model_id=model_id)
    elif provider == "anthropic":
         if not os.getenv("ANTHROPIC_API_KEY"):
             print("Error: ANTHROPIC_API_KEY not found.")
             sys.exit(1)
         llm_model = AnthropicModel(model_id=model_id)
    elif provider == "gemini":
         if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
              print("Error: GEMINI_API_KEY or GOOGLE_API_KEY not found.")
              sys.exit(1)
         llm_model = GeminiModel(model_id=model_id)
    else:
        print(f"Error: Unknown provider {provider}")
        sys.exit(1)

    # Load Serena tools
    print("Loading Serena tools...")
    serena_tools = get_serena_tools()
    print(f"Loaded {len(serena_tools)} tools from Serena.")

    # Initialize Agent
    agent = Agent(
        model=llm_model,
        tools=serena_tools,
        system_prompt="""You are a helpful QA Agent for a software repository.
        Your goal is to answer the user's question by actively exploring the codebase.
        
        You have access to a rich set of tools from the 'serena' library.
        
        Rules:
        1. Always start by understanding the directory structure if you are unsure where things are.
        2. Use relevant tools (e.g. `find_file`, `search_for_pattern`, `read_file`, `execute_shell_command`) to explore.
        3. Be concise in your final answer but provide sufficient technical detail.
        4. If you cannot find the answer, state what you tried and why you failed.
        """
    )

    print("Agent started. Processing query for provider:", provider)
    try:
        # Agent is callable
        response = agent(query)
        
        print("\n=== Agent Response ===")
        print(response)
        print("======================")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
