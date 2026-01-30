import os
import sys
import argparse
import strands
from strands import Agent
from unittest.mock import MagicMock
from serena.tools import ToolRegistry

# Map provider names to expected model strings or configuration
MODEL_MAPPING = {
    "openai": "gpt-5.2",
    "anthropic": "claude-4.5-sonnet",
    "gemini": "gemini-3.0-pro",
}

def get_serena_tools():
    """Dynamically load and wrap all Serena tools for Strands."""
    # Initialize a dummy agent for tool instantiation
    _mock_agent = MagicMock()
    _mock_agent.serena_config = MagicMock() 

    registry = ToolRegistry()
    tools = []
    
    # Instantiate all available tools
    # Note: ToolRegistry.get_all_tool_classes() returns a list of tool classes
    for tool_cls in registry.get_all_tool_classes():
        try:
            # Instantiate tool with mock agent
            tool_instance = tool_cls(_mock_agent)
            
            # The 'apply' method is the entry point for the tool
            func = tool_instance.apply
            
            # We need to wrap it to ensure strands picks up the correct name/doc
            # Since strands.tool is a decorator, we can apply it to the bound method.
            # However, we should ensure the name is descriptive (snake_case from serena).
            tool_name = tool_instance.get_name_from_cls()
            
            # Apply strands.tool decorator
            # strands.tool introspects the function. Bound methods work well with inspect.signature.
            wrapped_tool = strands.tool(func)
            
            # Override name/doc if necessary, though strands might have already read them.
            # Strands likely uses __name__ of the function.
            # We might want to set __name__ of the bound method? You can't set __name__ of a bound method easily.
            # But the 'wrapped_tool' returned by strands.tool serves as the tool definition.
            # If strands uses the function name, it might be 'apply'. We MUST change the name.
            
            # Strands likely creates a tool definition. If it supports 'name' arg in decorator, we should use it.
            # Previous inspection: strands.tool is a function. 
            # If strands.tool doesn't take name args, we might need a wrapper function.
            
            def wrapper(*args, **kwargs):
                return tool_instance.apply(*args, **kwargs)
            
            # Copy metadata manually which logic libraries respect
            wrapper.__name__ = tool_name
            wrapper.__doc__ = tool_instance.apply.__doc__
            # Attempt to copy signature for tool introspection (crucial for LLM)
            try:
                import inspect
                wrapper.__signature__ = inspect.signature(tool_instance.apply)
            except:
                pass

            # Now decorate
            final_tool = strands.tool(wrapper)
            tools.append(final_tool)
            
        except Exception as e:
            # Skip tools that fail to instantiate (e.g. might need complex dependencies)
            print(f"Warning: Failed to load tool {tool_cls.__name__}: {e}")
            continue
            
    return tools

def main():
    parser = argparse.ArgumentParser(description="GitHub Repository QA Agent")
    parser.add_argument("--query", "-q", type=str, help="Question to ask the agent")
    parser.add_argument("--provider", "-p", type=str, choices=MODEL_MAPPING.keys(), help="LLM Provider")
    parser.add_argument("--model", "-m", type=str, help="Specific model name (overrides provider default)")
    
    args = parser.parse_args()
    
    # Priority: Args > Env > Default
    provider = args.provider or os.getenv("PROVIDER", "openai")
    model_name_arg = args.model or os.getenv("MODEL_NAME")
    
    model_name = model_name_arg if model_name_arg else MODEL_MAPPING.get(provider, "gpt-4o")
    
    # Query might come from args or Env (for easier CI integration if needed)
    query = args.query
    if not query:
        print("Error: Query must be provided via --query argument.")
        sys.exit(1)
    
    print(f"Initializing QA Agent with model: {model_name} (Provider: {provider})")

    # Ensure API keys are present
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        sys.exit(1)
    elif provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        sys.exit(1)
    elif provider == "gemini" and not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
         print("Error: GEMINI_API_KEY or GOOGLE_API_KEY not found.")
         sys.exit(1)

    # Load Serena tools
    print("Loading Serena tools...")
    serena_tools = get_serena_tools()
    print(f"Loaded {len(serena_tools)} tools from Serena.")

    # Initialize Agent
    agent = Agent(
        model=model_name,
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
