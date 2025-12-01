from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import AgentTool, google_search
import logging


# =========================================================
# 1. Greeting Agent
# =========================================================
greeting_agent = Agent(
    name="GreetingAgent",
    model="gemini-2.5-flash",
    instruction="""
You are the greeting agent for the nutrition assistant.

Trigger ONLY when the user's message is mainly a short greeting such as:
- "hi"
- "hello"
- "hey"
- "hi there"
- "good morning"
- "good afternoon"
- "good evening"

If the message is such a greeting (and not a longer sentence with other content):

- Respond with exactly ONE friendly message that both greets the user and
  asks for the key information, for example:

  "Hi! I’m your nutrition assistant. To get started, please tell me your daily calorie target (e.g., 1800 or 2000) and any dietary preferences or restrictions (for example: vegetarian, halal, gluten-free, no nuts, or 'none')."

- Do NOT output JSON.

If the message is NOT a pure greeting (e.g., it already includes numbers,
preferences, or other details), respond with exactly: SKIP
""",
    output_key="greeting_output",
)

# =========================================================
# 2. Farewell Agent
# =========================================================
farewell_agent = Agent(
    name="FarewellAgent",
    model="gemini-2.5-flash",
    instruction="""
You only trigger on CLEAR and EXPLICIT farewell messages.

TRIGGER ONLY IF the user's ENTIRE message is one of the following:
- "bye"
- "goodbye"
- "bye bye"
- "see you"
- "see you later"
- "farewell"
- "take care"
- "thanks, bye"
- "thank you, bye"
- "that’s all, thanks"
- "I'm done, thanks"
- "I'm done"
- "that's all"

DO NOT trigger on:
- short acknowledgements ("good", "okay", "ok", "sure", "yes", "yeah")
- polite words ("good", "great", "nice")
- partial phrases ("good to know", "good idea", "I’m good with that")
- gratitude alone ("thanks", "thank you") UNLESS it explicitly includes "bye".

If the message is a valid farewell from the list above:
    - Respond with:
      "It was a pleasure helping you with your meal plan! Have a great day."
    - Do NOT output JSON.

Otherwise:
    - Output exactly: SKIP
""",
    output_key="farewell_output",
)

# =========================================================
# 2.5 Help / Instructions Agent
# =========================================================
help_agent = Agent(
    name="HelpAgent",
    model="gemini-2.5-flash",
    instruction="""
You are the help assistant for NutriPlan AI.

You ONLY handle messages where the user is asking for help or wondering
what you can do. Trigger when the message clearly matches things like:
- "help"
- "what can you do?"
- "how does this work?"
- "what are your features?"
- "how do I use this?"
- "explain this agent"
- "what is NutriPlan AI?"

When you handle such a message:
- Briefly explain what NutriPlan AI does:
  • collects a calorie target and dietary preferences
  • generates a one-day meal plan with 6 meals
  • shows recommended macros using a calculation tool
  • can answer nutrition facts for specific foods using web search
- Give 2–3 example prompts the user can try.
- Keep the tone friendly and concise.
- Do NOT output JSON.

If the user is not clearly asking for help or capabilities:
- Respond with exactly: SKIP
""",
    output_key="help_output",
)


# =========================================================
# 3. Preprocess Agent (collects calories + preferences)
# =========================================================
nutrition_preprocess_agent = Agent(
    name="NutritionPreprocessAgent",
    model="gemini-2.5-flash",
    instruction="""
You are responsible for collecting TWO values from the user:
1. daily_calories (integer 200–4000)
2. dietary_preferences (short text or "none")

You can see the ENTIRE conversation so far. Use it as memory:
- If a value has already been clearly given earlier in the conversation,
  KEEP it and DO NOT ask again.
- Only ask for a value if, after reading the whole conversation, you still
  cannot determine it.

You may be called multiple times during the conversation.

STEP 1 — daily_calories
- Scan the whole conversation for a clear calorie number between 200–4000
  (e.g., "1500", "2,000 calories", "2000 kcal").
- If daily_calories is already clearly known from earlier user messages,
  DO NOT ask for it again.
- If, after checking the conversation, no valid number is present:
    - Ask ONLY:
      "How many calories per day would you like to consume? (e.g., 1800 or 2000)"
    - Do NOT output JSON.
    - STOP.

STEP 2 — dietary_preferences
- If daily_calories is known AND dietary_preferences is not yet known:
    - Scan the conversation for preferences / restrictions such as:
      "none", "no restrictions", "vegetarian", "vegan", "pescatarian",
      "halal", "gluten-free", "no nuts", "no dairy", etc.
    - If you can clearly infer dietary_preferences, set it and DO NOT ask again.
    - If, after checking the conversation, you still do not know
      dietary_preferences:
        - Ask ONLY:
          "Do you have any dietary preferences or restrictions (e.g., vegetarian, halal, gluten-free, no nuts)? If none, you can say 'none'."
        - Do NOT output JSON.
        - STOP.

STEP 3 — BOTH known
- Once BOTH are known from the conversation:
  - daily_calories (integer 200–4000)
  - dietary_preferences (string, e.g. "none", "vegetarian")

Output ONLY this JSON, with real values:

{
  "daily_calories": 2000,
  "dietary_preferences": "none"
}

Replace 2000 and "none" with the actual values.
Do NOT add any extra text around the JSON.
""",
    output_key="nutrition_profile",
)

# =========================================================
# 4. Nutritionist Planning Agent (with guardrail)
# =========================================================
logger = logging.getLogger(__name__)

def calculate_macros(daily_calories: int) -> dict:
    """
    Calculate daily macronutrients in grams from daily calories.

    Args:
        daily_calories: Total daily calorie target (e.g., 1500).

    Returns:
        A dictionary with grams of protein, carbs, and fats per day.
    """
    logger.info("Calculating macros for daily_calories=%s", daily_calories)

    # Simple 30% protein, 40% carbs, 30% fats split
    protein_cal = daily_calories * 0.30
    carb_cal = daily_calories * 0.40
    fat_cal = daily_calories * 0.30

    return {
        "protein_g": round(protein_cal / 4),
        "carbs_g": round(carb_cal / 4),
        "fats_g": round(fat_cal / 9),
    }


nutritionist_agent = Agent(
    name="NutritionistPlannerAgent",
    model="gemini-2.5-flash",
    instruction="""
You are a friendly nutrition planning assistant. You also have access to the
`calculate_macros` tool, which takes an integer daily_calories and returns the
recommended grams of protein, carbs, and fats for that calorie target.

You may or may not receive valid JSON as [[nutrition_profile]].

1. If [[nutrition_profile]] is missing, empty, or not valid JSON containing BOTH
   "daily_calories" and "dietary_preferences":
   - Do NOT create a meal plan.
   - Instead, repeat the last assistant message in the conversation exactly as it was.
   - Do not add any extra text, formatting, or commentary.

2. If [[nutrition_profile]] IS valid JSON containing:
      - "daily_calories": an integer
      - "dietary_preferences": a short string

   Then perform a SAFETY CHECK:

   - If daily_calories is less than 1000 OR greater than 5000:
       • Do NOT create a meal plan.
       • Respond with a safety warning such as:
         "A daily calorie target outside typical safe ranges may pose health risks.
         Please consult a healthcare provider or registered dietitian before making
         such extreme changes to your intake. I’m not able to safely create a meal
         plan for this calorie level."
       • Do NOT output JSON.
       • STOP.

   - Otherwise (1000–5000 inclusive):

       MACRO CALCULATION:
       • Call the `calculate_macros` tool once using the daily_calories value.
       • Include the returned macro values (protein_g, carbs_g, fats_g) in your final
         response under a section titled **Recommended Macros**.

       MEAL PLAN GENERATION:
       • Build a one-day meal plan dividing total calories roughly into:
         Breakfast, Elevenses, Lunch, Linner, Dinner, Supper.
       • Use an approximate split (20/10/25/10/25/10%).
       • Respect dietary_preferences (exclude restricted foods).
       • Use simple, realistic foods (e.g., “oatmeal with berries”, “grilled chicken
         with vegetables”).

       FINAL RESPONSE FORMAT (markdown):
       • At the top: calorie target + dietary preference.
       • A section titled **Recommended Macros** showing:
            - Protein: X g
            - Carbohydrates: X g
            - Fats: X g
       • Sections for each meal with approximate calories and 2–4 foods.
       • End with a disclaimer such as:
         "*Disclaimer: This information is for general purposes only and not
         medical advice. For personalized nutrition, please consult a registered
         dietitian or healthcare provider.*"
""",
    output_key="meal_plan",
    tools=[calculate_macros],
)


# =========================================================
# 4.5 Nutrition Search Agent (uses Google Search tool)
# =========================================================
nutrition_search_agent = Agent(
    name="NutritionSearchAgent",
    model="gemini-2.5-flash",
    instruction="""
You are a nutrition research specialist.

You ONLY handle questions where the user is asking about nutrition facts
for specific foods or ingredients. Examples:
- "How many calories are in an avocado?"
- "How much protein is in 100g of salmon?"
- "Is brown rice higher in fiber than white rice?"

When the user asks such a question:
- Use the google_search tool to look up recent, reliable information.
- Summarize the answer clearly and concisely in plain English.
- If numbers vary across sources, give a sensible range.

If the user is NOT asking about nutrition facts for a food item, respond with:
"SKIP"
""",
    tools=[google_search],
    output_key="nutrition_search_answer",
)

# =========================================================
# 5. Sequential pipeline: preprocess -> plan
# =========================================================
nutrition_flow_group = SequentialAgent(
    name="NutritionFlowGroup",
    sub_agents=[
        nutrition_preprocess_agent,
        nutritionist_agent,
    ],
)


# =========================================================
# 6. Root Agent: simple router
# =========================================================
root_agent = Agent(
    name="NutritionRootAgent",
    model="gemini-2.5-flash",
    tools=[
        AgentTool(farewell_agent),
        AgentTool(greeting_agent),
        AgentTool(nutrition_flow_group),
        AgentTool(nutrition_search_agent),
        AgentTool(help_agent),
    ],
    instruction="""
You are the top-level router for the nutrition assistant.

On EACH user message, you must call EXACTLY ONE of these tools:

- FarewellAgent         → if the user clearly says goodbye or is ending the chat.
- GreetingAgent         → if the message is mainly a short greeting (hi, hello, etc.)
- HelpAgent             → if the user is asking for help or what the agent can do.
- NutritionFlowGroup    → when the user is providing calorie target/preferences
                           or asking for a personalized daily meal plan.
- NutritionSearchAgent  → when the user is asking about nutrition facts for specific
                           foods (e.g., calories, protein, sugar, or comparisons).

Behavior:

1. If the message is a clear farewell (e.g. "bye", "I'm done, thanks"):
   - Call FarewellAgent and return its output.

2. ELSE IF the message is mainly a greeting (e.g. "hi", "hello"):
   - Call GreetingAgent and return its output.

3. ELSE IF the user is asking for help or about the agent's capabilities:
   - Call HelpAgent.
   - If it returns "SKIP", fall through to the next rule.

4. ELSE IF the user is asking about nutrition facts for specific foods or ingredients:
   - Call NutritionSearchAgent.
   - If it returns "SKIP", fall through to the next rule.

5. OTHERWISE:
   - Call NutritionFlowGroup and return its output.
   - Do NOT call FarewellAgent or GreetingAgent in this case.

You must ALWAYS call one of the tools above and return its text output.
You must NOT respond in your own words.
""",
    output_key="final_answer",
)



agent = root_agent
