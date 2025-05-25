# Medical Report Generator using Gemini 2.5 Flash

This Python script uses Google Cloud's Vertex AI and the Gemini 2.5 Flash model to analyze medical conversation transcripts and generate structured medical reports.

## Features

- Analyzes doctor-patient conversation transcripts
- Generates structured medical reports with sections for:
  - Patient Details
  - Chief Complaint
  - Symptoms
  - Medical History
  - Physical Examination
  - Doctor's Assessment
  - Plan and Recommendations
- Supports multiple input formats (text files, JSON files, direct text)
- Saves reports in both text and JSON formats
- Compatible with existing transcription system

## Requirements

- Python 3.7+
- Google Cloud Project with Vertex AI API enabled
- Google Cloud credentials configured

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements_medical_report.txt
```

2. Set up Google Cloud credentials:
   - Create a service account in your Google Cloud Project
   - Download the service account key file
   - Set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
   ```

3. Enable the Vertex AI API in your Google Cloud Project:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

## Configuration

1. Edit the `PROJECT_ID` variable in the scripts:
   - In `medical_report_generator.py`, line 174
   - In `example_usage.py`, line 15

2. Replace `"your-project-id-here"` with your actual Google Cloud Project ID.

## Usage

### Basic Usage

```python
from medical_report_generator import MedicalReportGenerator

# Initialize the generator
generator = MedicalReportGenerator(project_id="your-project-id")

# Analyze a transcript
transcript = "Doctor: Hello, how are you feeling today? Patient: I have a headache..."
report = generator.analyze_transcript(transcript)

# Save the report
generator.save_report(report)
```

### Using with Existing Transcriptions

```python
# Load from your transcription JSON file
transcript = generator.load_transcript_from_file("transcriptions/all_transcriptions.json")
report = generator.analyze_transcript(transcript)
```

### Command Line Usage

Run the main script with a sample transcript:
```bash
python medical_report_generator.py
```

Run the example usage script:
```bash
python example_usage.py
```

## Input Formats Supported

### 1. Plain Text Files (.txt)
```
Doctor: Good morning, how are you feeling?
Patient: I've been having headaches...
```

### 2. JSON Files
```json
{
  "transcript": "Doctor: Hello... Patient: I feel..."
}
```

### 3. Transcription System JSON Format
```json
{
  "transcriptions": {
    "1": {
      "session_transcript": ["Doctor: Hello...", "Patient: I feel..."],
      "timestamp": "2025-01-01 10:00:00"
    }
  }
}
```

## Output Format

The generated medical report includes the following structured sections:

- **Patient Details**: Name, age, gender, contact info, visit date
- **Chief Complaint**: Primary reason for the visit
- **Symptoms**: Current symptoms, duration, severity
- **Medical History**: Past medical history, medications, allergies
- **Physical Examination**: Vital signs, physical findings, diagnostic tests
- **Doctor's Assessment**: Primary diagnosis, differential diagnosis
- **Plan and Recommendations**: Treatment plan, follow-up instructions
- **Notes**: Additional observations

## Example Output

```
## PATIENT DETAILS
- Name: Mrs. Johnson
- Age: Not specified
- Gender: Female
- Contact Information: Not mentioned in transcript
- Date of Visit: 2025-01-15

## CHIEF COMPLAINT
- Primary reason for visit: Persistent cough for two weeks

## SYMPTOMS
- Current Symptoms: Dry cough, fatigue, shortness of breath
- Duration: Two weeks
- Severity: Worsening
...
```

## Files Created

- `medical_report_generator.py` - Main generator class
- `example_usage.py` - Example usage scripts
- `requirements_medical_report.txt` - Dependencies
- Generated reports:
  - `medical_report_YYYYMMDD_HHMMSS.txt` - Text format
  - `medical_report_YYYYMMDD_HHMMSS.json` - JSON format with metadata

## Error Handling

The script includes comprehensive error handling for:
- Invalid or missing transcripts
- Google Cloud authentication issues
- File I/O errors
- API rate limits and timeouts

## Security Notes

- Never commit your Google Cloud service account keys to version control
- Use environment variables or Google Cloud's default authentication
- Ensure your Google Cloud Project has appropriate access controls
- Consider data privacy regulations when processing medical transcripts

## Troubleshooting

### Common Issues

1. **Authentication Error**
   - Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
   - Verify the service account has Vertex AI permissions

2. **Project Not Found**
   - Check that the project ID is correct
   - Ensure Vertex AI API is enabled

3. **Empty Reports**
   - Verify the transcript contains actual conversation content
   - Check that the input format is supported

4. **Rate Limiting**
   - The script includes automatic retry logic
   - For high-volume usage, consider implementing additional rate limiting

## License

This project is provided as-is for educational and development purposes. 