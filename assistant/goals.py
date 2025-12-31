# goals.py
class GoalEngine:
    def __init__(self, query_fn):
        self.query = query_fn

    async def decide_goal(self, user_input):
        prompt = f"""
        User said: "{user_input}"

        Decide ONE goal:
        - answer
        - ask_clarifying_question
        - reflect
        - take_action
        - remain_silent

        Return only the goal name.
        """
        # Using a fast model for goal detection
        goal = await self.query("tinyllama", prompt)
        return goal.strip().lower()
