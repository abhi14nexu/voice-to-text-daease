import json
import os
from datetime import datetime
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

class MedicalReportGenerator:
    def __init__(self, project_id="", location="us-central1", credentials_path=None):
        """
        Initialize the Medical Report Generator with Vertex AI
        
        Args:
            project_id (str): Google Cloud Project ID
            location (str): Vertex AI location
            credentials_path (str): Path to service account JSON file (optional)
        """
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI with optional credentials
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            vertexai.init(project=project_id, location=location, credentials=credentials)
            print(f"Using credentials from: {credentials_path}")
        else:
            # Use default credentials (environment variable or gcloud)
            vertexai.init(project=project_id, location=location)
            print("Using default credentials (environment variable or gcloud)")
        
        # Load Gemini 2.5 Flash model
        self.model = GenerativeModel("publishers/google/models/gemini-2.5-flash-preview-05-20")
        
    def create_medical_analysis_prompt(self, transcript):
        """
        Create a structured prompt for medical transcript analysis
        
        Args:
            transcript (str): The medical conversation transcript
            
        Returns:
            str: Formatted prompt for Gemini
        """
        prompt = f"""
You are an expert medical assistant tasked with analyzing a doctor-patient conversation transcript and creating a structured medical report. Please analyze the following transcript and extract information into the specified sections.

TRANSCRIPT:
{transcript}

Please provide a comprehensive analysis in the following structured format:

## PATIENT DETAILS
- Name: [Extract if mentioned, otherwise "Not specified"]
- Age: [Extract if mentioned, otherwise "Not specified"]
- Gender: [Extract if mentioned, otherwise "Not specified"]
- Contact Information: [Extract if mentioned, otherwise "Not specified"]
- Date of Visit: [Extract if mentioned, otherwise use today's date]

## CHIEF COMPLAINT
- Primary reason for visit: [Main concern or symptom that brought patient to doctor]

## SYMPTOMS
- Current Symptoms: [List all symptoms mentioned by patient]
- Duration: [How long symptoms have been present]
- Severity: [Mild/Moderate/Severe if mentioned]
- Associated Symptoms: [Related symptoms]

## MEDICAL HISTORY
- Past Medical History: [Previous illnesses, surgeries, hospitalizations]
- Current Medications: [List all medications mentioned]
- Allergies: [Any allergies mentioned]
- Family History: [Relevant family medical history]
- Social History: [Smoking, alcohol, lifestyle factors if mentioned]

## PHYSICAL EXAMINATION
- Vital Signs: [If mentioned]
- Physical Findings: [Any examination findings discussed]
- Diagnostic Tests: [Any tests performed or results discussed]

## DOCTOR'S ASSESSMENT
- Primary Diagnosis: [Main diagnosis or suspected condition]
- Differential Diagnosis: [Other possible conditions considered]
- Clinical Impression: [Doctor's overall assessment]

## PLAN AND RECOMMENDATIONS
- Treatment Plan: [Prescribed medications, procedures, treatments]
- Follow-up Instructions: [When to return, what to monitor]
- Lifestyle Recommendations: [Diet, exercise, lifestyle changes]
- Additional Tests: [Any further tests or referrals recommended]
- Patient Education: [Important information given to patient]

## NOTES
- Any additional important information or observations from the conversation

Please ensure all information is extracted accurately from the transcript. If certain information is not available in the transcript, clearly state "Not mentioned in transcript" rather than making assumptions.
"""
        return prompt
    
    def analyze_transcript(self, transcript):
        """
        Analyze medical transcript using Gemini 2.5 Flash
        
        Args:
            transcript (str): The medical conversation transcript
            
        Returns:
            str: Structured medical report
        """
        try:
            # Create the prompt
            prompt = self.create_medical_analysis_prompt(transcript)
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            print(f"Error analyzing transcript: {str(e)}")
            return None
    
    def load_transcript_from_file(self, file_path):
        """
        Load transcript from a file (supports .txt and .json)
        
        Args:
            file_path (str): Path to the transcript file
            
        Returns:
            str: Transcript content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                if file_path.endswith('.json'):
                    data = json.load(file)
                    # Handle different JSON structures
                    if isinstance(data, dict):
                        # If it's our transcription format
                        if 'transcriptions' in data:
                            # Get the latest transcription
                            transcriptions = data['transcriptions']
                            if transcriptions:
                                latest_key = max(transcriptions.keys(), key=int)
                                latest_transcript = transcriptions[latest_key]
                                return '\n'.join(latest_transcript.get('session_transcript', []))
                        # If it's a simple dict with transcript key
                        elif 'transcript' in data:
                            return data['transcript']
                        # If it's a dict with session_transcript
                        elif 'session_transcript' in data:
                            return '\n'.join(data['session_transcript'])
                    # If it's a list of strings
                    elif isinstance(data, list):
                        return '\n'.join(data)
                    else:
                        return str(data)
                else:
                    # Plain text file
                    return file.read()
        except Exception as e:
            print(f"Error loading transcript from file: {str(e)}")
            return None
    
    def save_report(self, report, output_path=None):
        """
        Save the medical report to a file
        
        Args:
            report (str): The generated medical report
            output_path (str): Path to save the report (optional)
            
        Returns:
            str: Path where the report was saved
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"medical_report_{timestamp}.txt"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(report)
            print(f"Report saved to: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error saving report: {str(e)}")
            return None

def main():
    """
    Main function to demonstrate the medical report generator
    """
    # Configuration
    PROJECT_ID = "daease-transcription"  # Your Google Cloud Project ID
    LOCATION = "us-central1"
    
    # Option 1: Use service account key file directly (replace with your actual file name)
    CREDENTIALS_PATH = "daease-transcription-4f98056e2b9c.json"  # Update this filename
    
    # Option 2: Use environment variable (comment out CREDENTIALS_PATH above)
    # CREDENTIALS_PATH = None
    
    # Initialize the generator
    if CREDENTIALS_PATH and os.path.exists(CREDENTIALS_PATH):
        generator = MedicalReportGenerator(project_id=PROJECT_ID, location=LOCATION, credentials_path=CREDENTIALS_PATH)
    else:
        print("Credentials file not found, using environment variable...")
        generator = MedicalReportGenerator(project_id=PROJECT_ID, location=LOCATION)
    
    # Example usage options:
    
    # Option 1: Use a sample transcript (for testing)
    sample_transcript = """
    Doctor: Good morning, Mrs. Johnson. How are you feeling today?
    
    Patient: Good morning, Doctor. I've been having this persistent cough for about two weeks now, and it's getting worse. I'm also feeling quite tired.
    
    Doctor: I see. Can you tell me more about the cough? Is it dry or are you bringing up any phlegm?
    
    Patient: It's mostly dry, but sometimes I do cough up a little bit of clear mucus. It's worse at night and in the morning.
    
    Doctor: Any fever or shortness of breath?
    
    Patient: I had a low-grade fever for a few days last week, but that's gone now. I do feel a bit short of breath when I climb stairs.
    
    Doctor: Have you been around anyone who's been sick recently?
    
    Patient: Yes, my grandson had a cold about three weeks ago when I was babysitting him.
    
    Doctor: I see. Are you taking any medications currently?
    
    Patient: Just my blood pressure medication, lisinopril 10mg daily, and a multivitamin.
    
    Doctor: Any allergies to medications?
    
    Patient: I'm allergic to penicillin - it gives me a rash.
    
    Doctor: Let me examine you. Your temperature is normal today, blood pressure is 130/80, which is well controlled. Your lungs sound a bit congested on the right side. I think you may have developed a respiratory infection.
    
    Patient: Is it serious?
    
    Doctor: It doesn't appear to be serious, but I'd like to prescribe an antibiotic to help clear this up. Since you're allergic to penicillin, I'll prescribe azithromycin. Take one tablet daily for 5 days. Also, get plenty of rest and drink lots of fluids.
    
    Patient: Should I come back if it doesn't get better?
    
    Doctor: Yes, if your symptoms don't improve in a week or if they get worse, please call the office. Also, if you develop a high fever or severe shortness of breath, come in immediately.
    
    Patient: Thank you, Doctor.
    
    Doctor: You're welcome. Take care, and I hope you feel better soon.
    """
    
    # Option 2: Load from file (uncomment to use)
    # transcript = generator.load_transcript_from_file("path/to/your/transcript.txt")
    # if transcript is None:
    #     print("Failed to load transcript from file")
    #     return
    
    # Option 3: Load from our transcription JSON file (uncomment to use)
    # transcript = generator.load_transcript_from_file("transcriptions/all_transcriptions.json")
    # if transcript is None:
    #     print("Failed to load transcript from transcriptions file")
    #     return
    
    # Use sample transcript for this example
    transcript = sample_transcript
    
    print("Analyzing medical transcript...")
    print("=" * 50)
    
    # Generate the medical report
    report = generator.analyze_transcript(transcript)
    
    if report:
        print("GENERATED MEDICAL REPORT:")
        print("=" * 50)
        print(report)
        print("=" * 50)
        
        # Save the report
        output_file = generator.save_report(report)
        
        # Optionally save as JSON for structured data
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "original_transcript": transcript,
            "generated_report": report,
            "model_used": "gemini-2.5-flash-preview-05-20"
        }
        
        json_output = output_file.replace('.txt', '.json') if output_file else 'medical_report.json'
        try:
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"Structured report also saved to: {json_output}")
        except Exception as e:
            print(f"Error saving JSON report: {str(e)}")
            
    else:
        print("Failed to generate medical report")

if __name__ == "__main__":
    main() 