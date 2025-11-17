import os
import requests
from io import BytesIO
from typing import List, Dict, Any, Union

# 1. Zooniverse and Gemini Libraries
from panoptes_client import Project, Subject
from google import genai
from google.genai import types

# Define the expected return type for a subject location entry
SubjectLocationType = Dict[str, str]

# --- Configuration ---
PROJECT_ID: str = "12345" # Placeholder for RGZ EMU Project ID (Find this in the Zooniverse URL)

# Gemini API Key environment variable name
GEMINI_API_KEY_ENV: str = "GEMINI_API_KEY"

# Define the classification prompt with specific tags
CLASSIFICATION_PROMPT: str = (
    "Classify the radio galaxy morphology in the 'Zoomed in' radio panel (top-left). "
    "Use one or more of the following hashtags to describe the structure: "
    "#triple #doublelobe #amorphous #amorphous-lobe #bent #traces_host_galaxy "
    "#core-jet #plume #core #hourglass #lobe #peculiar #wat #hybrid #blended "
    "#double #tail #jet #artefact #compact-lobe. "
    "Do not include any other text besides the hashtags and reasoning."
)

def get_project(project_id: str) -> Project:
    """
    Initializes and returns the Zooniverse Project object.

    Args:
        project_id: The unique identifier for the Zooniverse project.

    Returns:
        The panoptes_client.Project object.
    """
    print(f"Initializing Zooniverse Project ID: {project_id}...")
    return Project(id=project_id)

def download_subject_image(project: Project) -> Union[bytes, None]:
    """
    Fetches the first subject's image URL and downloads the image bytes.

    Args:
        project: The initialized panoptes_client.Project object.

    Returns:
        The raw image bytes if successful, otherwise None.
    """
    print("Fetching a subject...")
    
    # Get the first subject in the project
    subjects: List[Subject] = list(project.subjects.limit(1))

    if not subjects:
        print("Error: No subjects found. Check PROJECT_ID or project status.")
        return None

    subject: Subject = subjects[0]
    subject_id: str = subject.id
    
    # Zooniverse locations is a list of dictionaries; we assume the main image is the first one.
    locations: List[SubjectLocationType] = subject.locations
    if not locations:
        print(f"Error: Subject {subject_id} has no location data.")
        return None
        
    # Extract the URL from the first location dictionary (value of the single key-value pair)
    image_url: str = locations[0].values()[0]
    print(f"Subject ID: {subject_id}, Image URL: {image_url}")

    # Download the image data
    try:
        image_response: requests.Response = requests.get(image_url)
        image_response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        print("Image downloaded successfully.")
        return image_response.content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None

def classify_image_with_gemini(image_data: bytes, prompt: str) -> Union[str, None]:
    """
    Sends the image bytes and prompt to the Gemini API for classification.

    Args:
        image_data: The raw image bytes to be classified.
        prompt: The text prompt containing classification instructions and tags.

    Returns:
        The model's classification text (string) or None if an error occurs.
    """
    print("\n--- Sending Image to Gemini for Classification ---")
    
    try:
        # 1. Initialize the Gemini Client
        client = genai.Client()
        
        # 2. Create a Part object from the image bytes
        image_part: types.Part = types.Part.from_bytes(
            data=image_data,
            mime_type='image/jpeg' # Assuming Zooniverse images are JPEG
        )

        # 3. Call the Gemini model
        response: types.GenerateContentResponse = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, prompt]
        )

        # 4. Return the result
        return response.text.strip()

    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return None

def main() -> None:
    """
    Main function to execute the Zooniverse subject download and Gemini classification workflow.
    """
    # Check for Gemini API Key
    if not os.getenv(GEMINI_API_KEY_ENV):
        print(f"Error: Please set the {GEMINI_API_KEY_ENV} environment variable.")
        return

    # Step 1: Download Subject
    try:
        project: Project = get_project(PROJECT_ID)
    except Exception as e:
        print(f"Failed to initialize project: {e}")
        return

    image_bytes: Union[bytes, None] = download_subject_image(project)
    
    if image_bytes is None:
        return
    
    # Step 2: Classify Image
    classification_result: Union[str, None] = classify_image_with_gemini(image_bytes, CLASSIFICATION_PROMPT)

    if classification_result:
        print("-" * 35)
        print(f"Classification Prompt:\n{CLASSIFICATION_PROMPT}")
        print("-" * 35)
        print(f"🤖 Final Gemini Classification: {classification_result}")
    else:
        print("Classification failed or returned no result.")

if __name__ == "__main__":
    main()