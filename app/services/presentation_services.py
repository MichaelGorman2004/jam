from pdf2image import convert_from_bytes
from PIL import Image
import io
import speech_recognition as sr
import base64
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from pydub import AudioSegment


load_dotenv()

client = OpenAI(api_key=os.getenv('APIKEY'))

class PresentationEvaluator:

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def process_presentation(self, pdf_content: bytes, audio_bytes: bytes, dpi: int = 85, resize_factor: float = 0.4) -> str:
        # Process PDF slides
        images = self._convert_pdf_to_images(pdf_content, dpi, resize_factor)
        slides_feedback = self._grade_pdf_images(images)
        
        # Process audio pitch
        transcription = self._transcribe_audio(audio_bytes)
        pitch_evaluation = self._evaluate_pitch(transcription)

        # Combine results
        combined_result = {
            "slides_evaluation": json.loads(slides_feedback),
            "pitch_evaluation": pitch_evaluation
        }

        return json.dumps(combined_result)
    
    def _convert_pdf_to_images(self, pdf_content: bytes, dpi: int = 85, resize_factor: float =0.4) -> list[str]:
        # Function skeleton
        # Convert PDF pages to images with a lower DPI
        pages = convert_from_bytes(pdf_content, dpi=dpi)
        base64_images = []

        for page in pages:
            # Resize the image using the resize_factor
            width, height = page.size
            new_size = (int(width * resize_factor), int(height * resize_factor))
            resized_page = page.resize(new_size, Image.LANCZOS)

            # Convert the page to a bytes object
            image_bytes = io.BytesIO()
            resized_page.save(image_bytes, format='PNG')

            # Base64 encode the image bytes
            image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
            base64_images.append(image_base64)

        return base64_images

    def _grade_pdf_images(self, images: list[str]) -> str:
        PROMPT = """
        You are provided with a series of images representing the slides of a presentation. 
        Based on the following criteria:
        - Simplicity: Are the slides clear, concise, and focused on one main idea per slide?
        - Color and Typography: Are the font sizes readable, consistent, and do the colors maintain good contrast?
        - Structure and Whitespace: Is there sufficient whitespace to avoid clutter?
        - Graphics and Icons: Are images, charts, and icons used effectively to support the message?
        - Overall Impression: What is your overall impression of the presentation?
        - Proffesionalism: How professional does the presentation look and is the vocabulary used mature?
        Evaluate the presentation as a whole and provide an overall score from 0.0 to 100.0. Be specific eg. 87.3.
        Let the result be limited to just the score and three bullet points summarizing the main issues formatted in JSON with the schema 
        {
            "score": float,  // Overall score from 0.0 to 100.0
            "main_issues": [
                string,  // First main issue
                string,   // Second main issue
                string // Third main issue
            ]
        }
        Ensure that your response can be parsed as valid JSON.
        """
        # Prepare messages with the prompt and images
        messages = [
            {"role": "system", "content": PROMPT}
        ]

        # Add each image as a separate message
        for image_base64 in images:
            image_message = {
                "role": "user",
                "content": f"![slide](data:image/png;base64,{image_base64})"
            }
            messages.append(image_message)

        # Call OpenAI's GPT-4 API
        response = client.chat.completions.create(model="gpt-4o",  # use 'gpt-4-vision' for models that support images
        messages=messages)

        # Get the response text
        feedback = response.choices[0].message.content
        return feedback
    
    def _transcribe_audio(self, audio_bytes: bytes) -> str:
        # Convert MP3 bytes to WAV
        audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)

        # Transcribe WAV
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                return text
            except sr.UnknownValueError:
                return "Speech recognition could not understand the audio"
            except sr.RequestError as e:
                return f"Could not request results from speech recognition service; {e}"
    
    def _evaluate_pitch(self, transcription: str) -> dict:
        prompt = """
        Evaluate the following startup pitch transcription based on these criteria:

        1. Clarity of Message
           - Is the business idea clearly articulated?
           - Are the problem statement and solution easy to understand?

        2. Value Proposition
           - Does the speech emphasize what makes the solution unique?
           - Is the value to customers or users clearly explained?

        3. Structure and Flow
           - Is the speech logically organized with a clear beginning, middle, and end?
           - Are the transitions between points smooth?

        4. Engagement and Persuasiveness
           - Does the language capture attention and maintain interest?
           - Is the content delivered in an engaging tone, making a strong case for the solution?

        5. Relevance to Tech Industry
           - Does the pitch address a problem or opportunity that aligns with current tech trends?
           - Does it mention how the solution leverages technology or meets tech industry needs?

        6. Scalability and Growth Potential
           - Does the pitch highlight the potential for scaling the solution?
           - Are there references to market size or growth opportunities?

        Provide a score from 0 to 10 for each criterion and a brief explanation. Format your response as a JSON object with the following structure:

        {
            "clarity_of_message": {"score": float, "explanation": string},
            "value_proposition": {"score": float, "explanation": string},
            "structure_and_flow": {"score": float, "explanation": string},
            "engagement_and_persuasiveness": {"score": float, "explanation": string},
            "relevance_to_tech_industry": {"score": float, "explanation": string},
            "scalability_and_growth_potential": {"score": float, "explanation": string},
            "overall_score": float,
            "summary": string
        }

        Transcription:
        """

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": transcription}
            ]
        )

        evaluation = json.loads(response.choices[0].message.content)
        return evaluation

    def _process_audio(self, audio_bytes: bytes) -> str:
        transcription = self._transcribe_audio(audio_bytes)
        evaluation = self._evaluate_pitch(transcription)
        return json.dumps(evaluation)
    

    
    
