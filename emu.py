import os
import datetime
import requests
from io import BytesIO
from typing import List, Dict, Any, Union, Tuple

# 1. Zooniverse and Gemini Libraries
from panoptes_client import Project, Subject, Workflow, Panoptes, Classification
from google import genai
from google.genai import types

# Define the expected return type for a subject location entry
SubjectLocationType = Dict[str, str]

# --- Configuration ---
PROJECT_ID: str = "18567" # Radio Galaxy Zoo: EMU Project ID
WORKFLOW_ID: str = "25792" # Radio Galaxy Zoo: EMU Workflow ID
OUTPUT_DIR: str = r"h:\WAN_Project\galaxies"
BATCH_SIZE: int = 5  # Number of subjects to process per run

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
    print(f"Initializing Zooniverse Project: {project_id}...")
    if "/" in project_id:
        return Project.find(slug=project_id)
    return Project.find(id=project_id)

def download_subject_image(subject: Subject) -> Union[Tuple[bytes, str, str], Tuple[None, None, None]]:
    """
    Fetches a subject and its ID to maintain the scene_ID_slug convention.

    Args:
        subject: The panoptes_client.Subject object.

    Returns:
        A tuple of (image bytes, subject ID, extension) if successful, otherwise (None, None, None).
    """
    subject_id: str = subject.id

    # Zooniverse locations is a list of dictionaries; we assume the main image is the first one.
    locations: List[SubjectLocationType] = subject.locations
    if not locations:
        print(f"Error: Subject {subject_id} has no location data.")
        return None, None, None
        
    # Extract the URL from the first location dictionary (value of the single key-value pair)
    image_url: str = list(locations[0].values())[0]
    extension: str = os.path.splitext(image_url)[1] or ".jpg"
    print(f"Subject ID: {subject_id}, Image URL: {image_url} ({extension})")

    # Download the image data
    try:
        image_response: requests.Response = requests.get(image_url)
        image_response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        print("Image downloaded successfully.")
        return image_response.content, subject_id, extension
    except Exception as e:
        print(f"Download error: {e}")
        return None, None, None

def classify_image_with_gemini(client: genai.Client, image_data: bytes, prompt: str) -> Union[str, None]:
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
        # Determine correct MIME type
        mime_type = 'image/png' if extension.lower() == '.png' else 'image/jpeg'
        
        # 1. Create a Part object from the image bytes
        image_part: types.Part = types.Part.from_bytes(
            data=image_data,
            mime_type=mime_type
        )

        # 3. Call the Gemini model
        response: types.GenerateContentResponse = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(
                system_instruction="You are an expert astronomer. Provide classifications using only the requested hashtags and a brief reasoning. Do not use introductory phrases or conversational filler."
            )
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
    # Check for Vertex AI Project ID
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("Error: Please set the GOOGLE_CLOUD_PROJECT environment variable in config.bat.")
        return

    # Connect to Zooniverse (Required for posting classifications)
    username = os.getenv("PANOPTES_USERNAME")
    password = os.getenv("PANOPTES_PASSWORD")
    if username and password and "YOUR_ZOONIVERSE" not in username:
        print(f"Connecting to Zooniverse as {username}...")
        try:
            Panoptes.connect(username=username, password=password)
        except Exception as e:
            print(f"Failed to connect to Zooniverse: {e}")
            return
    else:
        print("Warning: Zooniverse credentials not found in config.bat. Results will not be posted.")

    # Step 1: Download Subject
    try:
        project: Project = get_project(PROJECT_ID)
    except Exception as e:
        print(f"Failed to initialize project: {e}")
        return

    # Step 1.1: Ensure output directory exists immediately
    print(f"Checking output directory: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Initialize the Gemini Client once
    client = genai.Client(
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION")
    )

    # Step 1.2: Fetch unclassified subjects
    try:
        print(f"Searching for {BATCH_SIZE} new subjects to process from Workflow {WORKFLOW_ID}...")
        workflow = Workflow.find(WORKFLOW_ID)
        subjects = Subject.where(workflow_id=WORKFLOW_ID, scope='unclassified')
    except Exception as e:
        print(f"Error fetching subjects: {e}")
        return

    # Cache existing local IDs to skip them
    existing_ids = {
        f.split('_')[-1].split('.')[0] 
        for f in os.listdir(OUTPUT_DIR) 
        if f.startswith(f"scene_{PROJECT_ID}_")
    }

    processed_count = 0
    for subject in subjects:
        subject_id = subject.id
        if subject_id in existing_ids:
            print(f"Subject {subject_id} already exists locally. Skipping.")
            continue

        processed_count += 1
        print(f"\n" + "="*50)
        print(f"Processing Subject {processed_count}/{BATCH_SIZE} (ID: {subject_id})")
        print("="*50)

        # Step 1.3: Download Subject Image
        image_bytes, subject_id, extension = download_subject_image(subject)
        
        if not image_bytes:
            print(f"Skipping Subject {subject_id}: No image data retrieved.")
            continue
        
        # Step 1.4: Save local reference immediately
        filename = os.path.join(OUTPUT_DIR, f"scene_{PROJECT_ID}_{subject_id}{extension}")
        try:
            with open(filename, "wb") as f:
                f.write(image_bytes)
            print(f"Successfully saved subject image to: {filename}")
        except Exception as e:
            print(f"Failed to save image locally: {e}")

        # Step 2: Classify Image
        classification_result = classify_image_with_gemini(client, image_bytes, CLASSIFICATION_PROMPT, extension)

        if classification_result:
            print(f"\n[Subject ID: {subject_id}]")
            print(f"🤖 Final Gemini Classification: {classification_result}")
            
            # Step 3: Post Classification back to Zooniverse
            if username and password:
                try:
                    classification = Classification(links={
                        'project': project.id,
                        'workflow': workflow.id,
                        'subjects': [subject.id]
                    })
                    classification.metadata.update({
                        'started_at': datetime.datetime.now().isoformat(),
                        'finished_at': datetime.datetime.now().isoformat(),
                        'user_agent': 'Gemini-EMU-Bot',
                    })
                    # We use 'T0' as the default task ID for the first task in the workflow
                    classification.annotations.append({'task': 'T0', 'value': classification_result})
                    classification.save()
                    print(f"Successfully posted classification for Subject {subject_id} to Zooniverse.")
                except Exception as e:
                    print(f"Failed to post classification to Zooniverse: {e}")
        else:
            print(f"Classification failed for Subject {subject_id}.")

        if processed_count >= BATCH_SIZE:
            break

    print(f"\nBatch complete. Processed {processed_count} subjects.")

if __name__ == "__main__":
    main()