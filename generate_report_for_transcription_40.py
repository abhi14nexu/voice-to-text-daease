#!/usr/bin/env python3
"""
Generate medical report for transcription #40 (typhoid fever case)
"""

from medical_report_generator import MedicalReportGenerator
import json
from datetime import datetime

def generate_report_for_transcription_40():
    """
    Generate medical report specifically for transcription #40
    """
    PROJECT_ID = "daease-transcription"
    generator = MedicalReportGenerator(project_id=PROJECT_ID, credentials_path="daease-transcription-4f98056e2b9c.json")
    
    # Load transcription #40
    try:
        with open("transcriptions/all_transcriptions.json", 'r') as f:
            data = json.load(f)
        
        transcription_40 = data['transcriptions']['40']
        transcript = '\n'.join(transcription_40['session_transcript'])
        
        print("MEDICAL CONVERSATION - TRANSCRIPTION #40")
        print("=" * 70)
        print("ORIGINAL TRANSCRIPT:")
        print("-" * 50)
        print(transcript)
        print("-" * 50)
        
        print(f"\nTranscription Details:")
        print(f"- ID: #40")
        print(f"- Timestamp: {transcription_40['timestamp']}")
        print(f"- Word Count: {transcription_40['word_count']} words")
        print(f"- Duration: {transcription_40['duration_seconds']} seconds")
        print(f"- Language: {transcription_40['language']}")
        
        print("\nGenerating detailed medical report...")
        print("=" * 70)
        
        # Generate medical report
        report = generator.analyze_transcript(transcript)
        
        if report:
            print("\nGENERATED MEDICAL REPORT:")
            print("=" * 70)
            print(report)
            print("=" * 70)
            
            # Save the report with specific filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"medical_report_transcription_40_{timestamp}.txt"
            generator.save_report(report, output_file)
            
            # Also save as comprehensive JSON
            report_data = {
                "report_generated_at": datetime.now().isoformat(),
                "source_transcription": {
                    "id": "40",
                    "timestamp": transcription_40['timestamp'],
                    "word_count": transcription_40['word_count'],
                    "duration_seconds": transcription_40['duration_seconds'],
                    "language": transcription_40['language']
                },
                "original_transcript": transcript,
                "generated_medical_report": report,
                "ai_model_used": "gemini-2.5-flash-preview-05-20",
                "analysis_type": "Comprehensive Medical Report",
                "case_summary": "Suspected typhoid fever case with fever, GI symptoms, and travel history"
            }
            
            json_output = f"medical_report_transcription_40_{timestamp}.json"
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 TEXT REPORT SAVED: {output_file}")
            print(f"📋 JSON REPORT SAVED: {json_output}")
            
            # Also create a summary file
            summary_file = f"case_summary_transcription_40_{timestamp}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("MEDICAL CASE SUMMARY - TRANSCRIPTION #40\n")
                f.write("=" * 50 + "\n\n")
                f.write("CASE TYPE: Suspected Typhoid Fever\n")
                f.write(f"DATE: {transcription_40['timestamp']}\n")
                f.write(f"CONSULTATION DURATION: {transcription_40['duration_seconds']} seconds\n\n")
                f.write("KEY SYMPTOMS:\n")
                f.write("- High fever (102-103°F)\n")
                f.write("- Weakness and fatigue\n")
                f.write("- Headache and body aches\n")
                f.write("- Night sweats\n")
                f.write("- Nausea and loss of appetite\n")
                f.write("- Loose stools and abdominal pain\n\n")
                f.write("RISK FACTORS:\n")
                f.write("- Recent consumption of street food\n")
                f.write("- Travel to rural area\n\n")
                f.write("RECOMMENDED TESTS:\n")
                f.write("- CBC (Complete Blood Count)\n")
                f.write("- Widal Test\n\n")
                f.write("TREATMENT PLAN:\n")
                f.write("- Antibiotics\n")
                f.write("- Hydration\n")
                f.write("- Rest for at least one week\n\n")
                f.write("=" * 50 + "\n")
                f.write("Full detailed report available in the JSON file.\n")
            
            print(f"📝 CASE SUMMARY SAVED: {summary_file}")
            
            print("\n✅ MEDICAL REPORT GENERATION COMPLETE!")
            print("All files have been saved in the current directory.")
            
        else:
            print("❌ Failed to generate medical report")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("Medical Report Generator - Transcription #40 Analysis")
    print("🏥 Analyzing typhoid fever consultation...")
    print()
    
    generate_report_for_transcription_40() 