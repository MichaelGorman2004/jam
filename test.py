from pdf2image import convert_from_bytes
from PIL import Image

import os
import json
import io
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the API key
api_key = os.getenv('APIKEY')

if not api_key:
    raise ValueError("No API key found. Make sure you have set the APIKEY in your .env file.")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def transcribe_audio_with_openai(audio_bytes):
    """
    Transcribes audio using the OpenAI Whisper API.
    
    Parameters:
    audio_bytes (bytes): Audio file content in bytes.
    
    Returns:
    str: Transcribed text from the audio.
    """
    try:
        # Create a file-like object from bytes
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = 'audio.mp3'  # Give a name to the file-like object

        # Call the Whisper API for transcription
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

        # Return the transcribed text
        return response.text

    except Exception as e:
        print(f"Error in transcription: {str(e)}")
        return ""

def evaluate_pitch(transcription: str) -> dict:
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

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcription}
        ]
    )

    evaluation = json.loads(response.choices[0].message.content)
    return evaluation

def process_audio(audio_bytes: bytes) -> str:
    transcription = transcribe_audio_with_openai(audio_bytes)
    evaluation = evaluate_pitch(transcription)
    return json.dumps(evaluation)

def main():
    # Path to the MP3 file
    mp3_path = "/Users/athinshetty/jam/medieval-gamer-voice-darkness-hunts-us-what-youx27ve-learned-stay-226596.mp3"
    
    # Check if the file exists
    if not os.path.exists(mp3_path):
        raise FileNotFoundError(f"MP3 file not found: {mp3_path}")
    
    # Read the MP3 file
    with open(mp3_path, 'rb') as audio_file:
        audio_content = audio_file.read()

    # Process the audio
    result = process_audio(audio_content)
    
    # Print the result
    print(json.dumps(json.loads(result), indent=2))

if __name__ == "__main__":
    main()
