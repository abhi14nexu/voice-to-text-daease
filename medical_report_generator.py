import json
import os
from datetime import datetime
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

class MedicalReportGenerator:
    def __init__(self, project_id, credentials_path=None, credentials=None):
        """
        Initialize the Medical Report Generator
        
        Args:
            project_id (str): Google Cloud Project ID
            credentials_path (str, optional): Path to service account JSON file
            credentials (google.oauth2.service_account.Credentials, optional): Credentials object
        """
        self.project_id = project_id
        
        # Use provided credentials or load from file
        if credentials:
            self.credentials = credentials
        elif credentials_path:
            self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
        else:
            raise ValueError("Either credentials or credentials_path must be provided")
        
        # Initialize Vertex AI
        vertexai.init(
            project=self.project_id,
            credentials=self.credentials
        )
        
        # Initialize the model
        self.model = GenerativeModel("gemini-2.0-flash-exp")

    def analyze_transcript(self, transcript):
        """
        Generate a structured medical report from a conversation transcript
        
        Args:
            transcript (str): The medical conversation transcript
            
        Returns:
            str: Formatted medical report
        """
        prompt = f"""
        You are an expert medical assistant. Analyze the following medical conversation transcript and generate a comprehensive, structured medical report. 

        **TRANSCRIPT:**
        {transcript}

        **INSTRUCTIONS:**
        Generate a detailed medical report with the following sections:

        ## Patient Information
        - Extract any mentioned patient demographics, age, gender, etc.
        - If not explicitly mentioned, note as "Not specified in transcript"

        ## Chief Complaint
        - Primary reason for the visit
        - Patient's main concerns in their own words

        ## History of Present Illness
        - Detailed description of current symptoms
        - Timeline and progression
        - Associated symptoms
        - Aggravating and relieving factors

        ## Past Medical History
        - Previous medical conditions
        - Previous surgeries or hospitalizations
        - Current medications (if mentioned)

        ## Physical Examination
        - Any examination findings mentioned
        - Vital signs if discussed

        ## Assessment
        - Clinical impression
        - Differential diagnoses
        - Severity assessment

        ## Plan
        - Diagnostic tests recommended
        - Treatment recommendations
        - Follow-up instructions
        - Patient education points

        ## Additional Notes
        - Any other relevant information
        - Recommendations for further evaluation

        **FORMAT REQUIREMENTS:**
        - Use clear, professional medical language
        - Be thorough but concise
        - If information is not available in the transcript, clearly state "Not mentioned in transcript"
        - Maintain patient confidentiality standards
        - Use bullet points for clarity where appropriate
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating medical report: {str(e)}"

    def generate_ai_assessment(self, transcript):
        """
        Generate an AI medical assessment with disease analysis and recommendations
        
        Args:
            transcript (str): The medical conversation transcript
            
        Returns:
            str: Formatted AI medical assessment
        """
        prompt = f"""
        You are an advanced AI medical diagnostic assistant. Analyze the following medical conversation transcript and provide a comprehensive medical assessment with disease analysis, severity evaluation, and next steps.

        **TRANSCRIPT:**
        {transcript}

        **INSTRUCTIONS:**
        Provide a detailed AI medical assessment with the following sections:

        ## Symptom Analysis
        - List and categorize all symptoms mentioned
        - Identify symptom patterns and relationships
        - Note symptom severity and duration

        ## Differential Diagnosis
        - List possible conditions based on symptoms
        - Rank by likelihood with brief reasoning
        - Include both common and serious conditions to consider

        ## Disease Severity Assessment
        - Evaluate urgency level (Low/Moderate/High/Critical)
        - Identify any red flag symptoms
        - Risk stratification

        ## Recommended Next Steps
        - Immediate actions needed
        - Diagnostic tests to consider
        - Specialist referrals if indicated

        ## Suggested Investigations
        - Laboratory tests
        - Imaging studies
        - Other diagnostic procedures
        - Priority order of investigations

        ## Warning Signs to Monitor
        - Symptoms that would require immediate medical attention
        - When to return for follow-up
        - Emergency situations to watch for

        ## Treatment Considerations
        - General treatment approaches
        - Lifestyle modifications
        - Medication considerations (general categories)

        ## Patient Education Priorities
        - Key points to explain to patient
        - Self-care instructions
        - Prevention strategies

        ## AI Confidence Assessment
        - Confidence level in assessment (High/Medium/Low)
        - Factors affecting confidence
        - Limitations of this analysis

        **IMPORTANT NOTES:**
        - This is an AI assessment for educational/reference purposes only
        - Always emphasize the need for professional medical evaluation
        - Do not provide specific medication dosages or definitive diagnoses
        - Highlight when immediate medical attention is needed
        - Be clear about limitations and uncertainties

        **FORMAT:**
        Use clear headings, bullet points, and professional medical language.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating AI assessment: {str(e)}"

    def generate_comprehensive_analysis(self, transcript):
        """
        Generate both medical report and AI assessment
        
        Args:
            transcript (str): The medical conversation transcript
            
        Returns:
            dict: Dictionary containing both analyses
        """
        try:
            medical_report = self.analyze_transcript(transcript)
            ai_assessment = self.generate_ai_assessment(transcript)
            
            return {
                'medical_report': medical_report,
                'ai_assessment': ai_assessment,
                'timestamp': json.dumps({"generated_at": "now"}, default=str)
            }
        except Exception as e:
            return {
                'error': f"Error generating comprehensive analysis: {str(e)}"
            }

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
    
    def create_ai_assessment_prompt(self, transcript):
        """
        Create a prompt specifically for AI medical assessment with disease analysis
        
        Args:
            transcript (str): The medical conversation transcript
            
        Returns:
            str: Formatted prompt for AI assessment
        """
        prompt = f"""
You are an expert AI medical assistant. Analyze the following doctor-patient conversation transcript and provide a comprehensive medical assessment. Focus on clinical reasoning, potential diagnoses, and evidence-based recommendations.

TRANSCRIPT:
{transcript}

Please provide your analysis in the following structured format:

## 🔍 SYMPTOM ANALYSIS
- **Primary Symptoms:** [List main symptoms with clinical significance]
- **Symptom Pattern:** [Describe the pattern, onset, progression]
- **Red Flags:** [Any concerning symptoms that require immediate attention]
- **Symptom Severity Score:** [Rate 1-10 with justification]

## 🩺 DIFFERENTIAL DIAGNOSIS
- **Most Likely Diagnosis:** [Primary suspected condition with confidence %]
- **Alternative Diagnoses:** [List 2-3 other possible conditions with likelihood]
- **Ruling Out:** [Serious conditions to exclude]
- **Clinical Reasoning:** [Explain the diagnostic thinking process]

## ⚠️ SEVERITY ASSESSMENT
- **Overall Severity:** [Mild/Moderate/Severe/Critical]
- **Urgency Level:** [Routine/Urgent/Emergency]
- **Risk Factors:** [Patient-specific risk factors]
- **Prognosis:** [Expected outcome with and without treatment]

## 🎯 RECOMMENDED NEXT STEPS
### Immediate Actions (0-24 hours):
- [List immediate steps needed]

### Short-term Actions (1-7 days):
- [List follow-up actions]

### Long-term Management (1+ weeks):
- [List ongoing care recommendations]

## 🧪 SUGGESTED INVESTIGATIONS
- **Essential Tests:** [Must-have diagnostic tests]
- **Additional Tests:** [Helpful but not critical tests]
- **Monitoring Parameters:** [What to track over time]

## 🚨 WARNING SIGNS
- **When to Seek Emergency Care:** [Red flag symptoms]
- **Follow-up Triggers:** [When to return for reassessment]

## 💊 TREATMENT CONSIDERATIONS
- **Pharmacological:** [Medication recommendations with rationale]
- **Non-pharmacological:** [Lifestyle, therapy recommendations]
- **Contraindications:** [What to avoid]

## 📋 PATIENT EDUCATION PRIORITIES
- **Key Points to Explain:** [Most important information for patient]
- **Lifestyle Modifications:** [Specific changes needed]
- **Compliance Factors:** [How to ensure treatment adherence]

## 🔮 AI CONFIDENCE ASSESSMENT
- **Diagnostic Confidence:** [High/Medium/Low with explanation]
- **Recommendation Strength:** [Strong/Moderate/Weak evidence base]
- **Limitations:** [What information is missing for better assessment]

**IMPORTANT DISCLAIMER:** This AI assessment is for educational and supportive purposes only. It should not replace professional medical judgment. All recommendations should be validated by qualified healthcare professionals before implementation.
"""
        return prompt
    
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
    
    # Option 1: Use service account key file directly (replace with your actual file name)
    CREDENTIALS_PATH = "daease-transcription-4f98056e2b9c.json"  # Update this filename
    
    # Option 2: Use environment variable (comment out CREDENTIALS_PATH above)
    # CREDENTIALS_PATH = None
    
    # Initialize the generator
    if CREDENTIALS_PATH and os.path.exists(CREDENTIALS_PATH):
        generator = MedicalReportGenerator(project_id=PROJECT_ID, credentials_path=CREDENTIALS_PATH)
    else:
        print("Credentials file not found, using environment variable...")
        generator = MedicalReportGenerator(project_id=PROJECT_ID)
    
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
            "model_used": "gemini-2.0-flash-exp"
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