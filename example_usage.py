#!/usr/bin/env python3
"""
Example usage of the Medical Report Generator

This script demonstrates how to use the MedicalReportGenerator class
to analyze transcripts from your existing transcription system.
"""

from medical_report_generator import MedicalReportGenerator

def analyze_latest_transcription():
    """
    Analyze the latest transcription from the transcriptions file
    """
    # Replace with your Google Cloud Project ID
    PROJECT_ID = "daease-transcription"
    
    # Initialize the generator
    generator = MedicalReportGenerator(project_id=PROJECT_ID)
    
    # Load the latest transcription from your existing file
    transcript = generator.load_transcript_from_file("transcriptions/all_transcriptions.json")
    
    if transcript:
        print("Found transcript:")
        print("-" * 50)
        print(transcript[:200] + "..." if len(transcript) > 200 else transcript)
        print("-" * 50)
        
        # Generate medical report
        print("\nGenerating medical report...")
        report = generator.analyze_transcript(transcript)
        
        if report:
            print("\nMEDICAL REPORT:")
            print("=" * 60)
            print(report)
            print("=" * 60)
            
            # Save the report
            generator.save_report(report)
        else:
            print("Failed to generate report")
    else:
        print("No transcript found or failed to load transcript")

def analyze_specific_transcription(transcription_id):
    """
    Analyze a specific transcription by ID
    
    Args:
        transcription_id (str): The ID of the transcription to analyze
    """
    PROJECT_ID = "daease-transcription"
    generator = MedicalReportGenerator(project_id=PROJECT_ID)
    
    # Load specific transcription
    import json
    try:
        with open("transcriptions/all_transcriptions.json", 'r') as f:
            data = json.load(f)
            
        if transcription_id in data.get('transcriptions', {}):
            transcript_data = data['transcriptions'][transcription_id]
            transcript = '\n'.join(transcript_data.get('session_transcript', []))
            
            if transcript.strip():
                print(f"Analyzing transcription #{transcription_id}")
                print(f"Date: {transcript_data.get('timestamp', 'Unknown')}")
                print(f"Language: {transcript_data.get('language', 'Unknown')}")
                print("-" * 50)
                
                report = generator.analyze_transcript(transcript)
                if report:
                    print("MEDICAL REPORT:")
                    print("=" * 60)
                    print(report)
                    print("=" * 60)
                    
                    # Save with specific filename
                    output_file = f"medical_report_#{transcription_id}.txt"
                    generator.save_report(report, output_file)
                else:
                    print("Failed to generate report")
            else:
                print(f"Transcription #{transcription_id} is empty")
        else:
            print(f"Transcription #{transcription_id} not found")
            
    except Exception as e:
        print(f"Error loading transcription: {str(e)}")

def analyze_custom_transcript(transcript_text):
    """
    Analyze a custom transcript provided as text
    
    Args:
        transcript_text (str): The transcript text to analyze
    """
    PROJECT_ID = "daease-transcription"
    generator = MedicalReportGenerator(project_id=PROJECT_ID)
    
    print("Analyzing custom transcript...")
    report = generator.analyze_transcript(transcript_text)
    
    if report:
        print("MEDICAL REPORT:")
        print("=" * 60)
        print(report)
        print("=" * 60)
        
        generator.save_report(report)
    else:
        print("Failed to generate report")

if __name__ == "__main__":
    print("Medical Report Generator - Example Usage")
    print("=" * 50)
    
    # Example 1: Analyze latest transcription
    print("\n1. Analyzing latest transcription...")
    analyze_latest_transcription()
    
    # Example 2: Analyze specific transcription (uncomment to use)
    # print("\n2. Analyzing specific transcription...")
    # analyze_specific_transcription("27")  # Replace with actual transcription ID
    
    # Example 3: Analyze custom transcript (uncomment to use)
    # custom_transcript = """
    # Doctor: Hello, how can I help you today?
    # Patient: I've been having headaches for the past week.
    # Doctor: Can you describe the pain?
    # Patient: It's a throbbing pain on the right side of my head.
    # """
    # print("\n3. Analyzing custom transcript...")
    # analyze_custom_transcript(custom_transcript) 