import logging
import streamlit as st
import time
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class ChatInterface:
    """Manages the chat interface and message handling."""
    
    @staticmethod
    def stream_response(response_data: Any, message_placeholder: Any) -> str:
        """
        Stream the response to the chat interface.
        
        Args:
            response_data: The response data to stream
            message_placeholder: The Streamlit placeholder to update
            
        Returns:
            str: The final response text
        """
        try:
            if isinstance(response_data, list):
                full_response = ""
                for item in response_data:
                    if isinstance(item, dict) and 'text' in item:
                        text = item['text']
                        text = text.replace('\n\n', '\n').strip()
                        full_response += text
                        message_placeholder.markdown(full_response)
                        time.sleep(0.003)
                return full_response
            elif isinstance(response_data, str):
                full_response = ""
                for char in response_data:
                    full_response += char
                    message_placeholder.markdown(full_response)
                    time.sleep(0.01)
                return full_response
            else:
                message_placeholder.markdown(str(response_data))
                return str(response_data)
        except Exception as e:
            error_msg = f"Error during streaming: {str(e)}"
            logger.error(error_msg)
            message_placeholder.markdown(str(response_data))
            return str(response_data)

    @staticmethod
    def display_messages(messages: List[Dict[str, str]]) -> None:
        """
        Display all messages in the chat history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
        """
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    @staticmethod
    def display_error(error: str, message_placeholder: Any = None) -> None:
        """
        Display an error message in the chat interface.
        
        Args:
            error: The error message to display
            message_placeholder: Optional placeholder for the message
        """
        if message_placeholder:
            message_placeholder.error(error)
        else:
            st.error(error) 