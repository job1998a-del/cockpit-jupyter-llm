# tools.py
import subprocess
import logging

logger = logging.getLogger(__name__)

def run_shell(cmd):
    """Execute a shell command and return the output."""
    try:
        # Security Note: In a real production environment, 
        # shell commands should be strictly sanitized or restricted.
        return subprocess.getoutput(cmd)
    except Exception as e:
        return f"Error executing shell: {str(e)}"

TOOLS = {
    "shell": run_shell
}

class ToolEngine:
    def __init__(self, query_fn):
        self.query = query_fn

    async def decide_tool(self, user_input):
        prompt = f"""
        User request: "{user_input}"

        Choose tool:
        - shell
        - none

        Return tool name only.
        """
        decision = await self.query("tinyllama", prompt)
        return decision.strip().lower()

    async def execute(self, tool_name, params):
        if tool_name in TOOLS:
            logger.info(f"Executing tool: {tool_name} with params: {params}")
            return TOOLS[tool_name](params)
        return "Tool not found."
