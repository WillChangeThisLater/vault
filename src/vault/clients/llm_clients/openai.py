from openai import OpenAI
from PIL import Image
import io
import base64
from vault.clients.llm_clients.base import BaseLLMClient

class LLMClient(BaseLLMClient):

    def __init__(self, model_id="gpt-4o-mini"):
        self.model_id = model_id
        self.client = OpenAI()

    def summarize(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def summarize_image(self, image: Image, prompt: str = "") -> str:
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        image_b64 = base64.b64encode(buffered.getvalue()).decode()

        if not prompt:
            prompt = "Summarize the image content."

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content
