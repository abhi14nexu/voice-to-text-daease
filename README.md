# Real-Time Voice Transcription App

This application uses Google Cloud Speech-to-Text API to perform real-time voice transcription through your microphone.

## Setup Instructions

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Cloud:
   - Create a Google Cloud project
   - Enable the Speech-to-Text API
   - Create a service account and download the JSON credentials file
   - Rename the credentials file to `google_credentials.json` and place it in the project root

3. Create a `.env` file in the project root with:
```
GOOGLE_APPLICATION_CREDENTIALS=google_credentials.json
```

## Running the Application

Run the Streamlit app with:
```bash
streamlit run app.py
```

## Features
- Real-time voice transcription
- Clean and intuitive user interface
- Adjustable microphone settings
- Text output display

## Requirements
- Python 3.7+
- Working microphone
- Google Cloud account with Speech-to-Text API enabled 