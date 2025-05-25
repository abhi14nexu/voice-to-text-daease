#!/usr/bin/env python3
"""
Test script to analyze existing transcriptions from your voice-to-text system
"""

from medical_report_generator import MedicalReportGenerator
import json

def test_with_existing_transcription():
    """
    Test the medical report generator with one of your existing transcriptions
    """
    PROJECT_ID = "daease-transcription"
    generator = MedicalReportGenerator(project_id=PROJECT_ID)
    
    # Load your transcriptions
    try:
        with open("transcriptions/all_transcriptions.json", 'r') as f:
            data = json.load(f)
        
        # Find transcriptions with actual content
        transcriptions_with_content = []
        for tid, tdata in data.get('transcriptions', {}).items():
            session_transcript = tdata.get('session_transcript', [])
            if session_transcript and any(text.strip() for text in session_transcript):
                word_count = tdata.get('word_count', 0)
                transcriptions_with_content.append((tid, tdata, word_count))
        
        if not transcriptions_with_content:
            print("No transcriptions with content found.")
            return
        
        # Sort by word count and get the one with most content
        transcriptions_with_content.sort(key=lambda x: x[2], reverse=True)
        
        print("Available transcriptions with content:")
        for i, (tid, tdata, word_count) in enumerate(transcriptions_with_content[:5]):
            timestamp = tdata.get('timestamp', 'Unknown')
            language = tdata.get('language', 'Unknown')
            print(f"{i+1}. ID #{tid} - {timestamp} - {word_count} words - {language}")
        
        # Use the one with most content
        best_tid, best_data, best_word_count = transcriptions_with_content[0]
        
        print(f"\nAnalyzing transcription #{best_tid} with {best_word_count} words...")
        print("=" * 60)
        
        # Get the transcript
        transcript = '\n'.join(best_data.get('session_transcript', []))
        
        print("ORIGINAL TRANSCRIPT:")
        print("-" * 40)
        print(transcript)
        print("-" * 40)
        
        # Generate medical report
        print("\nGenerating medical report...")
        report = generator.analyze_transcript(transcript)
        
        if report:
            print("\nGENERATED MEDICAL REPORT:")
            print("=" * 60)
            print(report)
            print("=" * 60)
            
            # Save the report with specific filename
            output_file = f"medical_report_transcription_{best_tid}.txt"
            generator.save_report(report, output_file)
            
            # Also save as JSON
            report_data = {
                "source_transcription_id": best_tid,
                "source_timestamp": best_data.get('timestamp'),
                "source_language": best_data.get('language'),
                "source_word_count": best_word_count,
                "original_transcript": transcript,
                "generated_report": report,
                "model_used": "gemini-2.5-flash-preview-05-20"
            }
            
            json_output = f"medical_report_transcription_{best_tid}.json"
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"Report saved to: {output_file}")
            print(f"JSON report saved to: {json_output}")
            
        else:
            print("Failed to generate medical report")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def analyze_transcription_38():
    """
    Specifically analyze transcription #38 which has the most content
    """
    PROJECT_ID = "daease-transcription"
    generator = MedicalReportGenerator(project_id=PROJECT_ID)
    
    # Transcription #38 content
    transcript_38 = """What were you saying, baby?
I don't know, where do we need to go?
Why?
Because I don't know.
You should know.
Hey chipra.
Hey, cutie.
Hey BA. Hi ba. Hey monkey.
Hindi."""
    
    print("Analyzing Transcription #38:")
    print("=" * 50)
    print("TRANSCRIPT:")
    print(transcript_38)
    print("=" * 50)
    
    # Note: This transcript doesn't appear to be medical in nature
    # But let's see what the AI makes of it
    report = generator.analyze_transcript(transcript_38)
    
    if report:
        print("\nGENERATED ANALYSIS:")
        print("=" * 50)
        print(report)
        print("=" * 50)
        
        generator.save_report(report, "analysis_transcription_38.txt")
    else:
        print("Failed to generate report")

if __name__ == "__main__":
    print("Testing Medical Report Generator with Your Transcriptions")
    print("=" * 60)
    
    # Test with existing transcriptions
    test_with_existing_transcription()
    
    print("\n" + "=" * 60)
    print("Note: Most of your current transcriptions appear to be test recordings")
    print("rather than actual medical conversations. For best results, try")
    print("recording an actual doctor-patient conversation or use the sample")
    print("transcript in medical_report_generator.py")
    print("=" * 60) 