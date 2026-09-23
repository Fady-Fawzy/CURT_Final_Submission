# Reflection

For missing item names, the assistant asks a question instead of guessing. If a name is partly typed, it uses the match only when there is one clear choice. For a small spelling mistake it suggests the closest inventory name, and for an unknown part it says that the part was not found. I chose these responses because they are easy to follow and avoid giving a made-up stock count or location.

I learned how to keep SQL queries in a small data-access layer, expose those functions through FastAPI, and let Gemini request only approved tools. The Streamlit page gave the same inventory a simple chat interface, and the session ID let the backend keep a short conversation history.

With more time, I would add a small way for a team member to update inventory, use a more robust name-matching approach, and save session history if the team needed it after a restart.
