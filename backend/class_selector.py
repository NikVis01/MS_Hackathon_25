import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

DEPLOYMENT_NAME = os.getenv("gpt-3.5-turbo")

def get_classes_from_prompt(prompt: str) -> list[str]:
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "Du är en AI som tolkar prompts och returnerar relevanta objektklasser att detektera i video."},
                {"role": "user", "content": f"Prompt: {prompt}. Vilka objektklasser borde jag detektera?"}
            ]
        )
        raw = response.choices[0].message.content
        return [cls.strip().lower() for cls in raw.split(',')]
    except Exception as e:
        # Logga gärna detta också
        print(f"Azure OpenAI error: {e}")
        return []