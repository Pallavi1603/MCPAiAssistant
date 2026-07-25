import asyncio
import os
import json
import sys
import traceback
from contextlib import AsyncExitStack
from typing import Any

from google import genai
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

