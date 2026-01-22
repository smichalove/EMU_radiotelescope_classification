# Radio Galaxy Zoo: EMU - Gemini Auto-Classifier

This repository contains a sophisticated automation tool designed to bridge citizen science and artificial intelligence. It automates the morphological classification of radio galaxies for the [Radio Galaxy Zoo: EMU](https://www.zooniverse.org/projects/hongming-tang/radio-galaxy-zoo-emu) project on Zooniverse using **Google Gemini 2.0 Flash** via Vertex AI.

## Features

- **Automated Retrieval**: Fetches unclassified subjects directly from the Zooniverse workflow.
- **Expert-Level AI Analysis**: Leverages Gemini 2.0 Flash to identify complex astronomical features such as lobes, jets, cores, and plumes.
- **Local Media Archiving**: Automatically saves downloaded images to a local directory (`h:\WAN_Project\galaxies`) using a standardized naming convention for verification and local cataloging.
- **Seamless Zooniverse Integration**: Authenticates and posts classifications directly back to the Zooniverse platform.
- **Intelligent Batch Processing**: Implements smart skipping by detecting previously processed subjects locally, optimizing API usage and reducing costs.

## Prerequisites

- Python 3.10+
- A Google Cloud Project with the **Vertex AI API** enabled.
- Google Cloud SDK installed and authenticated (`gcloud auth application-default login`).
- A Zooniverse account with access to the project.

## Setup

1. **Clone the repository** to your local machine.
2. **Configure Environment**: Edit `config.bat` with your specific details:
   - `GOOGLE_CLOUD_PROJECT`: Your Google Cloud Project ID.
   - `PANOPTES_USERNAME`: Your Zooniverse account email or username.
   - `PANOPTES_PASSWORD`: Your Zooniverse account password.
3. **Install Dependencies**: The `run_emu.bat` script handles this automatically, but you can manually install them via:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Simply run the provided batch file:

```batchfile
run_emu.bat
```

This will:
1. Load your configuration and credentials.
2. Connect to Zooniverse and Vertex AI.
3. Process a batch of unclassified subjects (configurable via `BATCH_SIZE`).
4. Save the images locally and upload the AI's findings to Zooniverse.

## Configuration

The following constants in `emu.py` can be adjusted to fit your workflow:
- `BATCH_SIZE`: The number of new subjects to process in a single run.
- `OUTPUT_DIR`: Local path where images are saved.
- `CLASSIFICATION_PROMPT`: The instructions and hashtags sent to Gemini.

## License
MIT