import boto3
import json
import os
from typing import Dict, List, Any, Optional

from bedrock_agentcore.memory import MemoryClient
from core.tools.tool_interface import Tool
from core.tools.tool_factory import ToolFactory
from core.logger import setup_logger

@ToolFactory.register_tool
class Chat_history_summarize_tool(Tool):

    memory_client = MemoryClient(region_name=os.getenv("AWS_REGION", "us-west-2")) if not hasattr(Tool, 'memory_client') else Tool.memory_client

    """
    Chat history summarize tool for retrieving and summarizing short-term memory
    from AWS Bedrock AgentCore Memory. This tool can be used across multiple agents
    to provide conversation context and history.
    """

    def __init__(self):
        """Initialize the tool with context support."""
        super().__init__()
        self.logger = setup_logger(name="ChatHistorySummarizeTool", level=os.getenv("LOG_LEVEL", "INFO"))
        self.logger.info("ChatHistorySummarizeTool initialized")

    def run(self, *args, **kwargs) -> str:
        """
        Retrieves and summarizes chat history for the current user session from short-term memory.
        Uses context provided by the agent to get memory_id, actor_id, and session_id.
        
        Args:
            max_turns (int, optional): Maximum number of conversation turns to retrieve. Defaults to 10.
            include_branch (str, optional): Specific branch name to retrieve. Defaults to None (main branch).
            format_type (str, optional): Format of output - "summary", "full", or "json". Defaults to "summary".
            
        Returns:
            str: A formatted summary of the chat history or JSON string if format_type is "json"
            
        Raises:
            ValueError: If required context parameters are missing
            Exception: If memory retrieval fails
        """
        # Get required parameters from context
        memory_id = self.get_context("memory_id")
        actor_id = self.get_context("actor_id") or self.get_context("user_id")  # Support both keys
        session_id = self.get_context("session_id")

        # Get optional parameters from kwargs or default to class attributes
        max_turns = kwargs.get("max_turns", 10)
        include_branch = kwargs.get("include_branch", None)
        format_type = kwargs.get("format_type", "summary").lower()
        
        if not memory_id:
            return "Memory ID not available in context. Cannot retrieve chat history."
        
        if not actor_id:
            return "Actor ID (user ID) not available in context. Cannot retrieve chat history."
            
        if not session_id:
            return "Session ID not available in context. Cannot retrieve chat history."

        try:
            # Retrieve the last K conversation turns from short-term memory
            turns = self.memory_client.get_last_k_turns(
                memory_id=memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=max_turns,
                branch_name=include_branch,
                include_branches=False,
                max_results=max_turns * 10  # Allow for multiple messages per turn
            )
            self.logger.info(f"Retrieved {len(turns)} turns from memory for actor_id={actor_id}, session_id={session_id}")
            self.logger.debug(f"Turns data: {turns}")

            if not turns:
                return "No chat history found for the current session."
            
            # Format the output based on requested format
            if format_type == "json":
                return json.dumps(turns, indent=2, default=str)
            elif format_type == "full":
                return self._format_full_history(turns)
            else:  # summary format (default)
                return self._format_summary(turns)
                
        except Exception as e:
            error_msg = f"Failed to retrieve chat history: {str(e)}"
            print(error_msg)  # Log for debugging
            return error_msg  # Return user-friendly error instead of raising
    
    def _format_summary(self, turns: List[List[Dict[str, Any]]]) -> str:
        """
        Create a concise summary of the conversation turns.
        
        Args:
            turns: List of conversation turns from memory
            
        Returns:
            str: Formatted summary string
        """
        if not turns:
            return "No conversation history available."
        
        summary_parts = [f"Chat History Summary ({len(turns)} turns):\n"]
        
        for i, turn in enumerate(turns, 1):
            turn_summary = f"Turn {i}: "
            user_messages = []
            assistant_messages = []
            
            for message in turn:
                role = message.get('role', '').upper()
                content = message.get('content', {})
                text = content.get('text', '') if isinstance(content, dict) else str(content)
                
                if role == 'USER':
                    user_messages.append(text[:100] + "..." if len(text) > 100 else text)
                elif role == 'ASSISTANT':
                    assistant_messages.append(text[:100] + "..." if len(text) > 100 else text)
            
            if user_messages:
                turn_summary += f"User: {' | '.join(user_messages)}"
            if assistant_messages:
                if user_messages:
                    turn_summary += " → "
                turn_summary += f"Assistant: {' | '.join(assistant_messages)}"
            
            summary_parts.append(turn_summary)
        
        return "\n".join(summary_parts)
    
    def _format_full_history(self, turns: List[List[Dict[str, Any]]]) -> str:
        """
        Create a detailed formatted view of the conversation history.
        
        Args:
            turns: List of conversation turns from memory
            
        Returns:
            str: Detailed formatted conversation string
        """
        if not turns:
            return "No conversation history available."
        
        formatted_parts = [f"Complete Chat History ({len(turns)} turns):\n" + "="*50]
        
        for i, turn in enumerate(turns, 1):
            formatted_parts.append(f"\n--- Turn {i} ---")
            
            for message in turn:
                role = message.get('role', 'UNKNOWN').upper()
                content = message.get('content', {})
                text = content.get('text', '') if isinstance(content, dict) else str(content)
                timestamp = message.get('timestamp', 'N/A')
                
                formatted_parts.append(f"{role}: {text}")
                if timestamp != 'N/A':
                    formatted_parts.append(f"  [Time: {timestamp}]")
        
        return "\n".join(formatted_parts)

    @property
    def name(self) -> str:
        """
        Return the name of the tool.
        """
        return "Chat_history_summarize_tool"

    @property
    def description(self) -> str:
        """
        Optional: Return a description of the tool.
        """
        return "Retrieves and summarizes chat history from the current conversation session. Automatically uses the current user and session context. Use this when users ask about previous conversations or want to review what was discussed earlier. Supports different output formats: 'summary' (default), 'full', or 'json'."
