from pdf2image import convert_from_path
from PIL import Image
import io
import base64
import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

client = OpenAI(api_key=os.getenv('APIKEY'))



def convert_pdf_to_base64_images(pdf_file, dpi=85, resize_factor=0.4):
    # Convert PDF pages to images with a lower DPI
    pages = convert_from_path(pdf_file, dpi=dpi)
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

PROMPT = """
You are provided with a series of images representing the slides of a presentation. 
Evaluate the presentation as a whole and provide an overall score from 0.0 to 100.0 based on the following criteria:
- Simplicity: Are the slides clear, concise, and focused on one main idea per slide?
- Color and Typography: Are the font sizes readable, consistent, and do the colors maintain good contrast?
- Structure and Whitespace: Is there sufficient whitespace to avoid clutter?
- Graphics and Icons: Are images, charts, and icons used effectively to support the message?
- Overall Impression: What is your overall impression of the presentation?
- Proffesionalism: How professional does the presentation look and is the vocabulary used mature?
Let the result be limited to just the score and two bullet points summarizing the main issues.
"""

def grade_pdf_with_openai(pdf_file):
    # Convert PDF to base64-encoded images
    base64_images = convert_pdf_to_base64_images(pdf_file)

    # Prepare messages with the prompt and images
    messages = [
        {"role": "system", "content": PROMPT}
    ]

    # Add each image as a separate message
    for image_base64 in base64_images:
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

# # Example usage
# pdf_file = "as.pdf"

# try:
#     feedback = grade_pdf_with_openai(pdf_file)
#     print("Slideshow Feedback:", feedback)
# except Exception as e:
#     print(str(e))


# def save_base64_images_to_directory(base64_images, directory='imagetest'):
#     # Create the directory if it doesn't exist
#     if not os.path.exists(directory):
#         os.makedirs(directory)

#     # Loop through each base64-encoded image
#     for idx, image_base64 in enumerate(base64_images):
#         # Decode the base64 image
#         image_data = base64.b64decode(image_base64)

#         # Create the file path
#         image_path = os.path.join(directory, f'slide_{idx+1}.png')

#         # Save the image as a PNG file
#         with open(image_path, 'wb') as image_file:
#             image_file.write(image_data)

#     print(f"All images have been saved to '{directory}'.")

# # Example usage with base64_images list
# save_base64_images_to_directory(convert_pdf_to_base64_images(pdf_file="Athin's Send Offhacka.pdf"))