import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Initiera FastAPI
app = FastAPI()

# Tillåt CORS (för frontend att kunna prata med backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Du kan begränsa detta till din frontend-domän i produktion
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🔑 Modell som matchar exakt det som frontend skickar (camelCase)
class Payload(BaseModel):
    feed_id: str
    detection_mode: str
    prompt: str

@app.post("/recieve")
async def receive_json(payload: Payload):
    result = update_yamnet_categories(payload.prompt)
    return {
        "status": "OK",
        "received": payload.dict(),
        "ai_response": result
    }


# 🔐 Ladda API-nycklar från .env
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")


# 🧠 Funktion som pratar med OpenAI
def update_yamnet_categories(prompt: str):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI that analyzes prompts and returns a JSON list of YAMNet sound categories that are relevant to the prompt. Return a JSON array of strings."
                },
                {
                    "role": "user",
                    "content": f"Prompt: {prompt}. Generate a JSON list of relevant YAMNet categories. Please create approximately 5 categories, preferably well-trained and common ones. JUST print the list, nothing else, not even a json tag. If the prompt you recieved has more than one argument, try not to generalize"
                }
            ]
        )

        raw_content = response.choices[0].message.content
        try:
            categories = json.loads(raw_content)
            print(categories)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"❌ JSON-fel: {e}")
            print(f"📄 Innehåll: {raw_content}")
            return {
                "status": "error",
                "message": "Invalid JSON from OpenAI",
                "yamnet_categories": []
            }

        # Spara resultat till fil
        with open('yamnet_categories.json', 'w') as f:
            json.dump(categories, f, indent=4)

        return {
            "status": "success",
            "message": "YAMNet categories updated successfully",
            "yamnet_categories": categories
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "yamnet_categories": []
        }


# 🏁 Starta appen (endast om du kör lokalt)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)