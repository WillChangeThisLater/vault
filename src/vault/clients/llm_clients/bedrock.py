import boto3
import logging
import io
from PIL import Image
from PIL import UnidentifiedImageError
from vault.clients.llm_clients.base import BaseLLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockLLMClient(BaseLLMClient):

    def __init__(self, model_id="amazon.nova-pro-v1:0"):
        self._model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name="us-east-1")

    def summarize(self, prompt: str) -> str:
        message = {
            "role": "user",
            "content": [
                {"text": prompt},
            ]
        }

        # Call the Converse API
        response = self.client.converse(
            modelId=self._model_id,
            messages=[message]
        )

        # Extract and return the text summary from the assistant’s message
        output_message = response['output']['message']
        for content in output_message['content']:
            if "text" in content:
                logger.info(f"Image summary: {content['text']}")
                return content["text"]

        raise ValueError("No LLM summarization found")


    def summarize_image(self, image: Image, prompt: str = "") -> str:
        try:
            with io.BytesIO() as output:
                # Detect the format of the input image
                image_format = image.format
                if image_format is None:
                    raise ValueError("Image format could not be determined")

                # Convert image if necessary
                image.save(output, format=image_format)
                image_bytes = output.getvalue()

            if not prompt:
                prompt = "Summarize the content of the image."

            # Prepare the message payload
            message = {
                "role": "user",
                "content": [
                    {"text": prompt},
                    {"image": {
                        "format": image_format.lower(),
                        "source": {"bytes": image_bytes}
                    }}
                ]
            }

            # Call the Converse API
            response = self.client.converse(
                modelId=self._model_id,
                messages=[message]
            )

            # Extract and return the text summary from the assistant’s message
            output_message = response['output']['message']
            for content in output_message['content']:
                if "text" in content:
                    logger.info(f"Image summary: {content['text']}")
                    return content["text"]

            raise ValueError("No LLM summarization found")

        except UnidentifiedImageError:
            logger.error("The provided file could not be identified as an image. Please provide a valid image file.")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
