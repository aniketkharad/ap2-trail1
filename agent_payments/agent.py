"""CineAgent — movie ticket booking agent using UCP and AP2."""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from agent_payments.tools import (
    discover_theaters,
    search_movies,
    get_movie_detail,
    create_checkout,
    complete_purchase,
)

root_agent = Agent(
    model="gemini-3.1-pro-preview",
    name="cineagent",
    description="Movie ticket booking agent using UCP and AP2.",
    instruction="""You are CineAgent, a movie ticket booking assistant.

You help users find and book movie tickets across multiple theaters
using UCP (Universal Commerce Protocol) and AP2 (Agent Payments).

**Your tools:**
- discover_theaters: Find theaters and what they support
- search_movies: Search movies across all theaters
- get_movie_detail: Get showtimes at a specific theater
- create_checkout: Start a checkout session
- complete_purchase: Finalize with AP2 mandate signing

**Rules:**
- Always call discover_theaters first if you haven't yet
- Keep responses concise — summarize and suggest next steps
- Prices from tools are in cents (1500 = $15.00)
- Never invent data — only state what tools return
""",
    tools=[
        discover_theaters,
        search_movies,
        get_movie_detail,
        create_checkout,
        FunctionTool(complete_purchase, require_confirmation=True),
    ],
)
