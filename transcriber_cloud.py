import os
import json
from datetime import datetime
import streamlit as st
from google.cloud import speech
from google.oauth2 import service_account
from medical_report_generator import MedicalReportGenerator
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import base64

# Transcription storage settings
TRANSCRIPTIONS_DIR = "transcriptions"
TRANSCRIPTIONS_FILE = os.path.join(TRANSCRIPTIONS_DIR, "all_transcriptions.json")

# Language settings
SUPPORTED_LANGUAGES = {
    "English (US)": "en-US",
    "Hindi": "hi-IN",
    "English (India)": "en-IN"
}

def get_credentials():
    """Get Google Cloud credentials from Streamlit secrets or file"""
    try:
        # Try Streamlit secrets first (for cloud deployment)
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            credentials_info = dict(st.secrets["gcp_service_account"])
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            return credentials
        else:
            # Fallback to local file
            credentials = service_account.Credentials.from_service_account_file(
                "daease-transcription-4f98056e2b9c.json"
            )
            return credentials
    except Exception as e:
        st.error(f"Failed to load credentials: {str(e)}")
        st.error("Please check your Google Cloud credentials configuration.")
        return None

def load_transcription_counter():
    """Load the current transcription counter and data"""
    if os.path.exists(TRANSCRIPTIONS_FILE):
        with open(TRANSCRIPTIONS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('counter', 0), data.get('transcriptions', {})
    return 0, {}

def save_transcription(transcript_text, language_code):
    """Save transcription with counter and metadata"""
    os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
    
    # Load existing data
    counter, transcriptions = load_transcription_counter()
    
    # Ensure counter is an integer and increment
    counter = int(counter) + 1
    
    # Create new transcription entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_transcription = {
        'timestamp': timestamp,
        'transcript': transcript_text,
        'word_count': len(transcript_text.split()),
        'language': language_code
    }
    
    # Add to transcriptions dict
    transcriptions[str(counter)] = new_transcription
    
    # Save updated data
    data = {
        'counter': counter,
        'transcriptions': transcriptions,
        'last_updated': timestamp
    }
    
    with open(TRANSCRIPTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    return counter

def transcribe_audio_file(audio_file, language_code):
    """Transcribe uploaded audio file using Google Cloud Speech-to-Text"""
    try:
        credentials = get_credentials()
        if not credentials:
            return None
            
        client = speech.SpeechClient(credentials=credentials)
        
        # Read audio file
        audio_content = audio_file.read()
        
        # Configure recognition
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_code,
            enable_automatic_punctuation=True,
        )
        
        # Perform transcription
        response = client.recognize(config=config, audio=audio)
        
        # Extract transcript
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "
        
        return transcript.strip()
        
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return None

def generate_medical_report(transcript):
    """Generate medical report using Google Cloud Vertex AI"""
    try:
        PROJECT_ID = "daease-transcription"
        credentials = get_credentials()
        if not credentials:
            return None
            
        generator = MedicalReportGenerator(
            project_id=PROJECT_ID, 
            credentials=credentials
        )
        
        # Generate the medical report
        report = generator.analyze_transcript(transcript)
        return report
        
    except Exception as e:
        st.error(f"Error generating medical report: {str(e)}")
        return None

def generate_ai_assessment(transcript):
    """Generate AI medical assessment"""
    try:
        PROJECT_ID = "daease-transcription"
        credentials = get_credentials()
        if not credentials:
            return None
            
        generator = MedicalReportGenerator(
            project_id=PROJECT_ID, 
            credentials=credentials
        )
        
        # Generate the AI assessment
        assessment = generator.generate_ai_assessment(transcript)
        return assessment
        
    except Exception as e:
        st.error(f"Error generating AI assessment: {str(e)}")
        return None

def create_pdf_report(report_text, transcript_text, transcription_id=None):
    """Create a PDF report from the medical report text"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Build the PDF content
        story = []
        
        # Title
        title = f"Medical Report"
        if transcription_id:
            title += f" - Transcription #{transcription_id}"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        # Generated date
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Medical Report Section
        if report_text:
            story.append(Paragraph("MEDICAL REPORT", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # Split report into paragraphs and add them
            report_paragraphs = report_text.split('\n')
            for para in report_paragraphs:
                if para.strip():
                    if para.startswith('##'):
                        # Section headers
                        story.append(Paragraph(para.replace('##', '').strip(), styles['Heading3']))
                    elif para.startswith('-'):
                        # Bullet points
                        story.append(Paragraph(para, styles['Normal']))
                    else:
                        # Regular paragraphs
                        story.append(Paragraph(para, styles['Normal']))
                    story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 30))
        
        # Original Transcript Section
        story.append(Paragraph("ORIGINAL TRANSCRIPT", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        if transcript_text:
            transcript_paragraphs = transcript_text.split('\n')
            for para in transcript_paragraphs:
                if para.strip():
                    story.append(Paragraph(para, styles['Normal']))
                    story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error creating PDF: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="Medical Voice Transcriber", 
        layout="wide",
        page_icon="🏥",
        initial_sidebar_state="collapsed"
    )
    
    # Modern minimalist CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        font-family: 'Inter', sans-serif;
        background-color: #fafbfc;
    }
    
    .app-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
    }
    
    .app-title {
        color: white;
        font-size: 2.2rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .app-subtitle {
        color: rgba(255, 255, 255, 0.85);
        font-size: 1rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    
    .card-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .report-container {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1.25rem;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .assessment-container {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1.25rem;
        border-left: 4px solid #74b9ff;
        margin: 1rem 0;
    }
    
    .stButton > button {
        border-radius: 8px !important;
        border: none !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
        height: 2.75rem !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
    }
    
    .stButton > button[kind="secondary"] {
        background: #f8f9fa !important;
        color: #495057 !important;
        border: 1px solid #dee2e6 !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # App Header
    st.markdown("""
    <div class="app-header">
        <h1 class="app-title">🏥 Medical Voice Transcriber</h1>
        <p class="app-subtitle">AI-Powered Medical Conversation Analysis (Cloud Version)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'current_transcript' not in st.session_state:
        st.session_state.current_transcript = ""
    if 'medical_report' not in st.session_state:
        st.session_state.medical_report = None
    if 'ai_assessment' not in st.session_state:
        st.session_state.ai_assessment = None
    if 'last_transcription_id' not in st.session_state:
        st.session_state.last_transcription_id = None
    
    # Main content
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Input Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">📝 Input Method</div>', unsafe_allow_html=True)
        
        # Input tabs
        tab1, tab2 = st.tabs(["📁 Upload Audio File", "✍️ Text Input"])
        
        with tab1:
            st.markdown("**Upload an audio file for transcription**")
            
            # Language selection
            selected_language = st.selectbox(
                "Select Language",
                options=list(SUPPORTED_LANGUAGES.keys()),
                index=0
            )
            
            # File upload
            uploaded_file = st.file_uploader(
                "Choose an audio file",
                type=['wav', 'mp3', 'm4a', 'flac'],
                help="Supported formats: WAV, MP3, M4A, FLAC"
            )
            
            if uploaded_file is not None:
                st.audio(uploaded_file, format='audio/wav')
                
                if st.button("🎤 Transcribe Audio", type="primary", use_container_width=True):
                    with st.spinner("🤖 Transcribing audio..."):
                        language_code = SUPPORTED_LANGUAGES[selected_language]
                        transcript = transcribe_audio_file(uploaded_file, language_code)
                        
                        if transcript:
                            st.session_state.current_transcript = transcript
                            # Save transcription
                            transcription_id = save_transcription(transcript, language_code)
                            st.session_state.last_transcription_id = transcription_id
                            st.success(f"✅ Transcription completed! (ID: {transcription_id})")
                        else:
                            st.error("❌ Failed to transcribe audio")
        
        with tab2:
            st.markdown("**Enter or paste text directly**")
            
            text_input = st.text_area(
                "Medical Conversation Text",
                height=200,
                placeholder="Enter the medical conversation text here...",
                help="Paste or type the medical conversation you want to analyze"
            )
            
            if st.button("📝 Use This Text", type="primary", use_container_width=True):
                if text_input.strip():
                    st.session_state.current_transcript = text_input.strip()
                    # Save transcription
                    transcription_id = save_transcription(text_input.strip(), "manual-input")
                    st.session_state.last_transcription_id = transcription_id
                    st.success(f"✅ Text saved! (ID: {transcription_id})")
                else:
                    st.warning("⚠️ Please enter some text")
        
        # Display current transcript
        if st.session_state.current_transcript:
            st.markdown("---")
            st.markdown('<div class="card-header">📄 Current Transcript</div>', unsafe_allow_html=True)
            st.text_area(
                "Transcript",
                st.session_state.current_transcript,
                height=150,
                label_visibility="collapsed"
            )
            
            # Analysis buttons
            st.markdown("---")
            st.markdown('<div class="card-header">🏥 AI Analysis</div>', unsafe_allow_html=True)
            
            analysis_col1, analysis_col2, analysis_col3 = st.columns([1, 1, 1])
            
            with analysis_col1:
                if st.button("📋 Medical Report", type="primary", use_container_width=True):
                    with st.spinner("🤖 Generating report..."):
                        st.session_state.medical_report = generate_medical_report(st.session_state.current_transcript)
                        if st.session_state.medical_report:
                            st.success("✅ Report generated!")
                        else:
                            st.error("❌ Generation failed")
            
            with analysis_col2:
                if st.button("🩺 AI Assessment", type="primary", use_container_width=True):
                    with st.spinner("🧠 Generating assessment..."):
                        st.session_state.ai_assessment = generate_ai_assessment(st.session_state.current_transcript)
                        if st.session_state.ai_assessment:
                            st.success("✅ Assessment generated!")
                        else:
                            st.error("❌ Generation failed")
            
            with analysis_col3:
                if st.session_state.medical_report or st.session_state.ai_assessment:
                    with st.popover("⚙️ Actions", use_container_width=True):
                        if st.session_state.medical_report:
                            pdf_data = create_pdf_report(
                                st.session_state.medical_report,
                                st.session_state.current_transcript,
                                st.session_state.last_transcription_id
                            )
                            if pdf_data:
                                filename = f"medical_report_{st.session_state.last_transcription_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                st.download_button(
                                    label="📄 Download PDF",
                                    data=pdf_data,
                                    file_name=filename,
                                    mime="application/pdf",
                                    use_container_width=True
                                )
            
            # Display results
            if st.session_state.medical_report or st.session_state.ai_assessment:
                st.markdown("---")
                
                if st.session_state.medical_report and st.session_state.ai_assessment:
                    tab1, tab2 = st.tabs(["📋 Medical Report", "🩺 AI Assessment"])
                    
                    with tab1:
                        st.markdown('<div class="report-container">', unsafe_allow_html=True)
                        st.markdown(st.session_state.medical_report)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with tab2:
                        st.markdown('<div class="assessment-container">', unsafe_allow_html=True)
                        st.markdown(st.session_state.ai_assessment)
                        st.markdown('</div>', unsafe_allow_html=True)
                
                elif st.session_state.medical_report:
                    st.markdown("#### 📋 Medical Report")
                    st.markdown('<div class="report-container">', unsafe_allow_html=True)
                    st.markdown(st.session_state.medical_report)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                elif st.session_state.ai_assessment:
                    st.markdown("#### 🩺 AI Assessment")
                    st.markdown('<div class="assessment-container">', unsafe_allow_html=True)
                    st.markdown(st.session_state.ai_assessment)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        # History Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">📚 Transcription History</div>', unsafe_allow_html=True)
        
        _, transcriptions = load_transcription_counter()
        
        if transcriptions:
            # Summary metrics
            total_transcriptions = len(transcriptions)
            total_words = sum(data.get('word_count', 0) for data in transcriptions.values())
            
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Total Sessions", total_transcriptions)
            with metric_col2:
                st.metric("Total Words", f"{total_words:,}")
            
            st.markdown("---")
            
            # History list
            sorted_transcriptions = sorted(transcriptions.items(), key=lambda x: int(x[0]), reverse=True)
            for counter, data in sorted_transcriptions[:10]:  # Show last 10
                language_flag = "🇺🇸" if data.get('language') == 'en-US' else "🇮🇳" if data.get('language') in ['hi-IN', 'en-IN'] else "📝" if data.get('language') == 'manual-input' else "🌐"
                
                with st.expander(f"#{counter} • {data['timestamp'][:16]} • {language_flag}", expanded=False):
                    # Session info
                    info_col1, info_col2 = st.columns(2)
                    with info_col1:
                        st.caption(f"📊 {data['word_count']} words")
                    with info_col2:
                        lang_display = "Manual Input" if data.get('language') == 'manual-input' else data.get('language', 'Unknown')
                        st.caption(f"🌐 {lang_display}")
                    
                    # Transcript preview
                    transcript_text = data.get('transcript', '')
                    if transcript_text:
                        if len(transcript_text) > 150:
                            st.text(transcript_text[:150] + "...")
                            if st.button(f"👁️ View Full", key=f"view_{counter}", use_container_width=True):
                                st.text_area("Full Transcript", transcript_text, height=120, key=f"full_{counter}")
                        else:
                            st.text(transcript_text)
                        
                        # Quick actions
                        action_col1, action_col2 = st.columns(2)
                        with action_col1:
                            if st.button(f"📋 Report", key=f"report_{counter}", use_container_width=True):
                                with st.spinner("Generating..."):
                                    report = generate_medical_report(transcript_text)
                                    if report:
                                        st.success("Generated!")
                                        with st.expander("Medical Report", expanded=True):
                                            st.markdown(report)
                        
                        with action_col2:
                            if st.button(f"🩺 Assessment", key=f"assess_{counter}", use_container_width=True):
                                with st.spinner("Generating..."):
                                    assessment = generate_ai_assessment(transcript_text)
                                    if assessment:
                                        st.success("Generated!")
                                        with st.expander("AI Assessment", expanded=True):
                                            st.markdown(assessment)
                    else:
                        st.caption("No transcript content")
        else:
            st.info("📭 No transcriptions yet. Upload an audio file or enter text to get started!")
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 