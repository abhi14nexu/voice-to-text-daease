import os
import queue
import threading
import time
from datetime import datetime
import streamlit as st
import pyaudio
from google.cloud import speech
from google.oauth2 import service_account
import json
from medical_report_generator import MedicalReportGenerator
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import base64

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms chunks
CHANNELS = 1

# Transcription storage settings
TRANSCRIPTIONS_DIR = "transcriptions"
TRANSCRIPTIONS_FILE = os.path.join(TRANSCRIPTIONS_DIR, "all_transcriptions.json")

# Language settings
SUPPORTED_LANGUAGES = {
    "English (US)": "en-US",
    "Hindi": "hi-IN",
    "English (India)": "en-IN"
}

# Maximum duration for a single streaming request (in seconds)
MAX_STREAMING_DURATION = 270  # 4.5 minutes to be safe

def load_transcription_counter():
    """Load the current transcription counter and data"""
    if os.path.exists(TRANSCRIPTIONS_FILE):
        with open(TRANSCRIPTIONS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('counter', 0), data.get('transcriptions', {})
    return 0, {}

def save_transcription(full_transcript, session_transcript, language_code):
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
        'full_transcript': full_transcript,
        'session_transcript': session_transcript,
        'word_count': sum(len(text.split()) for text in session_transcript),
        'duration_seconds': None,  # Will be added in stop_recording
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

class AudioTranscriber:
    def __init__(self, credentials_path, language_code="en-US"):
        try:
            # Create credentials and client
            self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = speech.SpeechClient(credentials=self.credentials)
            self.language_code = language_code
            
        except Exception as e:
            st.error(f"Failed to initialize Speech-to-Text client: {str(e)}")
            st.stop()
            
        self.audio_queue = queue.Queue()
        self.transcript_queue = queue.Queue()
        self.is_recording = False
        self.full_transcript = []
        self.current_session = []
        self.start_time = None
        self.stream_start_time = None
        self.current_interim = ""
        
        # Configure the recognition with standard settings
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=RATE,
                language_code=language_code,
                enable_automatic_punctuation=True
            ),
            interim_results=True,
        )

    def should_restart_stream(self):
        """Check if we should restart the streaming request"""
        if not self.stream_start_time:
            return False
        return (datetime.now() - self.stream_start_time).total_seconds() >= MAX_STREAMING_DURATION

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for PyAudio to process audio chunks"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def process_audio(self):
        """Process audio chunks and send to Google Speech-to-Text"""
        while self.is_recording:
            try:
                # Create a generator for streaming requests
                def request_generator():
                    while self.is_recording and not self.should_restart_stream():
                        try:
                            audio_data = self.audio_queue.get(timeout=1)
                            if audio_data:
                                request = speech.StreamingRecognizeRequest(audio_content=audio_data)
                                yield request
                        except queue.Empty:
                            continue
                        except Exception as e:
                            continue

                # Start streaming recognition
                self.stream_start_time = datetime.now()
                requests = request_generator()
                responses = self.client.streaming_recognize(self.streaming_config, requests)
                
                # Process responses
                for response in responses:
                    if not self.is_recording:
                        break
                    
                    if self.should_restart_stream():
                        break
                        
                    if not response.results:
                        continue
                    
                    result = response.results[0]
                    if not result.alternatives:
                        continue
                    
                    transcript = result.alternatives[0].transcript
                    
                    if result.is_final:
                        if transcript.strip():  # Only add non-empty transcripts
                            self.full_transcript.append(transcript)
                            self.current_session.append(transcript)
                            self.transcript_queue.put(("final", transcript))
                            print(f"Final transcript: {transcript}")  # Debug print
                        self.current_interim = ""
                    else:
                        self.current_interim = transcript
                        self.transcript_queue.put(("interim", transcript))
                        
            except Exception as e:
                if self.is_recording:  # Only show error if we're still supposed to be recording
                    print(f"Error in audio processing: {str(e)}")  # Debug print
                continue  # Continue to retry if there's an error

    def start_recording(self):
        """Start the recording and transcription process"""
        self.is_recording = True
        self.full_transcript = []
        self.current_session = []
        self.current_interim = ""
        self.start_time = datetime.now()
        self.stream_start_time = None
        
        print(f"Starting recording with language: {self.language_code}")  # Debug print
        
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Find input device
            input_device_index = None
            info = self.audio.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            
            for i in range(numdevices):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info.get('maxInputChannels') > 0:
                    if input_device_index is None:
                        input_device_index = i
            
            if input_device_index is None:
                raise Exception("No input device found")
            
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=CHUNK,
                stream_callback=self.audio_callback
            )
            
            # Start processing thread
            self.process_thread = threading.Thread(target=self.process_audio)
            self.process_thread.daemon = True
            self.process_thread.start()
            
            self.stream.start_stream()
            
        except Exception as e:
            st.error(f"Failed to start recording: {str(e)}")
            self.is_recording = False

    def stop_recording(self):
        """Stop the recording and transcription process"""
        print(f"Stopping recording. Current session has {len(self.current_session)} transcripts")  # Debug print
        
        self.is_recording = False
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'audio'):
            self.audio.terminate()
        if hasattr(self, 'process_thread'):
            self.process_thread.join()
        
        # Calculate duration
        duration_seconds = None
        if self.start_time:
            duration_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # Ensure we have the complete transcript
        final_transcript = self.full_transcript.copy()
        final_session = self.current_session.copy()
        
        print(f"Final transcript length: {len(final_transcript)}")  # Debug print
        print(f"Final session length: {len(final_session)}")  # Debug print
        
        # Only save if we have actual content
        if final_session and any(text.strip() for text in final_session):
            # Save transcription and get counter
            counter = save_transcription(final_transcript, final_session, self.language_code)
            
            # Update duration in saved transcription
            if duration_seconds:
                _, transcriptions = load_transcription_counter()
                if str(counter) in transcriptions:
                    transcriptions[str(counter)]['duration_seconds'] = duration_seconds
                    data = {
                        'counter': counter,
                        'transcriptions': transcriptions,
                        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    with open(TRANSCRIPTIONS_FILE, 'w') as f:
                        json.dump(data, f, indent=2)
            
            return counter, final_session
        else:
            print("No transcription content to save")  # Debug print
            return None, []

    def get_current_display_text(self):
        """Get the current text to display (final + interim)"""
        display_text = ""
        if self.current_session:
            display_text = "\n".join(self.current_session)
        if self.current_interim:
            if display_text:
                display_text += "\n" + self.current_interim
            else:
                display_text = self.current_interim
        return display_text

def generate_medical_report(transcript):
    """Generate medical report using Google Cloud Vertex AI"""
    try:
        PROJECT_ID = "daease-transcription"
        generator = MedicalReportGenerator(
            project_id=PROJECT_ID, 
            credentials_path="daease-transcription-4f98056e2b9c.json"
        )
        
        # Generate the medical report
        report = generator.analyze_transcript(transcript)
        return report
        
    except Exception as e:
        st.error(f"Error generating medical report: {str(e)}")
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
        story.append(Paragraph("MEDICAL REPORT", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Split report into paragraphs and add them
        if report_text:
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

def get_pdf_download_link(pdf_data, filename):
    """Generate a download link for PDF data"""
    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📄 Download Medical Report PDF</a>'
    return href

def main():
    st.set_page_config(
        page_title="Medical Voice Transcriber", 
        layout="wide",
        page_icon="🏥",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for modern design
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        text-align: center;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* Control Panel */
    .control-panel {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        border: 1px solid #e1e8ed;
    }
    
    /* Status Indicators */
    .status-recording {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        text-align: center;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(255,107,107,0.3);
        animation: pulse 2s infinite;
    }
    
    .status-idle {
        background: linear-gradient(135deg, #a8e6cf, #7fcdcd);
        color: #2d3436;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        text-align: center;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(168,230,207,0.3);
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Card Styling */
    .transcript-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e1e8ed;
        margin-bottom: 1rem;
    }
    
    .history-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    
    /* Medical Report Styling */
    .medical-report {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(240,147,251,0.3);
    }
    
    .report-content {
        background: white;
        color: #2d3436;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1rem;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Button Styling */
    .stButton > button {
        border-radius: 25px !important;
        border: none !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15) !important;
    }
    
    /* Download Button */
    .download-section {
        background: linear-gradient(135deg, #74b9ff, #0984e3);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    
    /* Language Selector */
    .language-selector {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 2px solid #e1e8ed;
    }
    
    /* Metrics */
    .metric-card {
        background: linear-gradient(135deg, #a29bfe, #6c5ce7);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(162,155,254,0.3);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: #f8f9fa !important;
        border-radius: 8px !important;
        border: 1px solid #e9ecef !important;
    }
    
    /* Text Area Styling */
    .stTextArea > div > div > textarea {
        border-radius: 10px !important;
        border: 2px solid #e1e8ed !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.1) !important;
    }
    
    /* Selectbox Styling */
    .stSelectbox > div > div > select {
        border-radius: 10px !important;
        border: 2px solid #e1e8ed !important;
        font-weight: 500 !important;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, #00b894, #00a085) !important;
        border-radius: 10px !important;
        border: none !important;
    }
    
    .stError {
        background: linear-gradient(135deg, #e17055, #d63031) !important;
        border-radius: 10px !important;
        border: none !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fdcb6e, #e17055) !important;
        border-radius: 10px !important;
        border: none !important;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    </style>
    """, unsafe_allow_html=True)
    
    # Main Header
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🏥 Medical Voice Transcriber</h1>
        <p class="main-subtitle">AI-Powered Real-time Medical Conversation Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state variables
    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = "English (US)"
    if 'transcriber' not in st.session_state:
        st.session_state.transcriber = None
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    if 'current_transcript' not in st.session_state:
        st.session_state.current_transcript = []
    if 'medical_report' not in st.session_state:
        st.session_state.medical_report = None
    if 'last_recording_id' not in st.session_state:
        st.session_state.last_recording_id = None
    if 'generating_report' not in st.session_state:
        st.session_state.generating_report = False
    if 'pdf_data' not in st.session_state:
        st.session_state.pdf_data = None
    
    # Language selection
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 2])
    
    # Control Panel
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    
    control_col1, control_col2, control_col3, control_col4 = st.columns([2, 1.5, 1.5, 3])
    
    with control_col1:
        st.markdown('<div class="language-selector">', unsafe_allow_html=True)
        st.markdown("**🌐 Language Selection**")
        selected_language = st.selectbox(
            "",
            options=list(SUPPORTED_LANGUAGES.keys()),
            index=list(SUPPORTED_LANGUAGES.keys()).index(st.session_state.selected_language),
            key="language_select"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if selected_language != st.session_state.selected_language:
            st.session_state.selected_language = selected_language
            st.session_state.transcriber = None
            st.experimental_rerun()
    
    # Initialize transcriber if needed
    if st.session_state.transcriber is None:
        st.session_state.transcriber = AudioTranscriber(
            "daease-transcription-4f98056e2b9c.json",
            language_code=SUPPORTED_LANGUAGES[selected_language]
        )
    
    # Load existing transcriptions
    _, transcriptions = load_transcription_counter()
    
    with control_col2:
        if st.button("🎙️ Start Recording", disabled=st.session_state.is_recording, type="primary", key="start_btn"):
            st.session_state.transcriber.start_recording()
            st.session_state.is_recording = True
            st.session_state.current_transcript = []
            st.session_state.medical_report = None
            st.session_state.generating_report = False
            st.session_state.pdf_data = None
            st.experimental_rerun()
    
    with control_col3:
        if st.button("⏹️ Stop Recording", disabled=not st.session_state.is_recording, type="secondary", key="stop_btn"):
            counter, session_transcript = st.session_state.transcriber.stop_recording()
            st.session_state.is_recording = False
            
            if counter is not None and session_transcript:
                st.session_state.current_transcript = session_transcript
                st.session_state.medical_report = generate_medical_report("\n".join(session_transcript))
                st.session_state.last_recording_id = counter
                st.session_state.generating_report = True
                st.session_state.pdf_data = create_pdf_report(st.session_state.medical_report, "\n".join(session_transcript), counter)
                st.success(f"✅ Recording saved (ID: {counter})")
            else:
                st.warning("⚠️ No speech detected in this recording. Please try speaking louder or closer to the microphone.")
                st.session_state.current_transcript = []
                st.session_state.medical_report = None
                st.session_state.last_recording_id = None
                st.session_state.generating_report = False
                st.session_state.pdf_data = None
            
            st.experimental_rerun()
    
    with control_col4:
        if st.session_state.is_recording:
            st.markdown("""
            <div class="status-recording">
                🔴 Recording in Progress...
                <br><small>Listening for medical conversation</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-idle">
                ⚪ Ready to Record
                <br><small>Click Start Recording to begin</small>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Create two columns for transcript and history
    transcript_col, history_col = st.columns([3, 2])
    
    with transcript_col:
        st.markdown('<div class="transcript-card">', unsafe_allow_html=True)
        st.markdown(f"### 🎤 Live Transcription ({selected_language})")
        
        # Show current or last session transcript
        if st.session_state.is_recording:
            # Show live transcription
            current_text = st.session_state.transcriber.get_current_display_text()
            if current_text:
                st.text_area("🔊 Live Transcript", current_text, height=150, key="live_transcript")
            else:
                st.info("🎧 Listening... Please speak into your microphone.")
                
        elif st.session_state.current_transcript:
            st.markdown("### 📝 Current Session Transcript")
            st.text_area("Session Transcript", "\n".join(st.session_state.current_transcript), height=200, key="current_session")
            
            # Medical Report Generation Section
            st.markdown("---")
            st.markdown("### 🏥 Medical Report Generation")
            
            col_report1, col_report2, col_report3 = st.columns([1, 1, 1])
            
            with col_report1:
                if st.button("🏥 Generate Medical Report", type="primary", disabled=st.session_state.generating_report, key="generate_report"):
                    with st.spinner("🤖 Generating medical report using AI..."):
                        st.session_state.generating_report = True
                        transcript_text = "\n".join(st.session_state.current_transcript)
                        st.session_state.medical_report = generate_medical_report(transcript_text)
                        
                        if st.session_state.medical_report:
                            # Create PDF
                            st.session_state.pdf_data = create_pdf_report(
                                st.session_state.medical_report, 
                                transcript_text, 
                                st.session_state.last_recording_id
                            )
                            st.success("✅ Medical report generated successfully!")
                        else:
                            st.error("❌ Failed to generate medical report")
                        
                        st.session_state.generating_report = False
                        st.experimental_rerun()
            
            with col_report2:
                if st.session_state.medical_report and st.session_state.pdf_data:
                    filename = f"medical_report_{st.session_state.last_recording_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=st.session_state.pdf_data,
                        file_name=filename,
                        mime="application/pdf",
                        type="secondary",
                        key="download_pdf"
                    )
            
            with col_report3:
                if st.session_state.medical_report:
                    if st.button("🗂️ Save to Folder", key="save_folder"):
                        try:
                            # Save text report
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            text_filename = f"medical_reports/medical_report_transcription_{st.session_state.last_recording_id}_{timestamp}.txt"
                            os.makedirs("medical_reports", exist_ok=True)
                            
                            with open(text_filename, 'w', encoding='utf-8') as f:
                                f.write(f"Medical Report - Transcription #{st.session_state.last_recording_id}\n")
                                f.write("=" * 60 + "\n\n")
                                f.write(st.session_state.medical_report)
                                f.write("\n\n" + "=" * 60 + "\n")
                                f.write("ORIGINAL TRANSCRIPT:\n")
                                f.write("\n".join(st.session_state.current_transcript))
                            
                            # Save PDF report
                            if st.session_state.pdf_data:
                                pdf_filename = f"medical_reports/medical_report_transcription_{st.session_state.last_recording_id}_{timestamp}.pdf"
                                with open(pdf_filename, 'wb') as f:
                                    f.write(st.session_state.pdf_data)
                            
                            st.success(f"💾 Reports saved to medical_reports folder!")
                        except Exception as e:
                            st.error(f"❌ Error saving reports: {str(e)}")
            
            # Display Medical Report
            if st.session_state.medical_report:
                st.markdown("---")
                st.markdown("""
                <div class="medical-report">
                    <h3 style="margin: 0; color: white;">🏥 Generated Medical Report</h3>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">AI-Powered Analysis using Google Cloud Vertex AI</p>
                    <div class="report-content">
                """, unsafe_allow_html=True)
                
                st.markdown(st.session_state.medical_report)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
                
                # Show report metadata
                with st.expander("📊 Report Details & Metadata"):
                    meta_col1, meta_col2 = st.columns(2)
                    with meta_col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <strong>Transcription ID</strong><br>
                            #{st.session_state.last_recording_id}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <strong>AI Model</strong><br>
                            Gemini 2.5 Flash
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with meta_col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <strong>Report Word Count</strong><br>
                            {len(st.session_state.medical_report.split())} words
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <strong>Source Length</strong><br>
                            {len(' '.join(st.session_state.current_transcript).split())} words
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.write(f"**Generated at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Processing Platform:** Google Cloud Vertex AI")
                    
        elif st.session_state.last_recording_id and str(st.session_state.last_recording_id) in transcriptions:
            last_recording = transcriptions[str(st.session_state.last_recording_id)]
            st.markdown("### 📋 Last Session Transcript")
            st.text_area("Session Transcript", "\n".join(last_recording['session_transcript']), height=200, key="last_session")
        else:
            st.info("🎙️ No transcription available. Start recording to begin.")
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    with history_col:
        st.markdown('<div class="history-card">', unsafe_allow_html=True)
        st.markdown("### 📚 Transcription History")
        
        if transcriptions:
            # Show summary stats
            total_transcriptions = len(transcriptions)
            total_words = sum(data.get('word_count', 0) for data in transcriptions.values())
            
            stats_col1, stats_col2 = st.columns(2)
            with stats_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <strong>{total_transcriptions}</strong><br>
                    Total Sessions
                </div>
                """, unsafe_allow_html=True)
            
            with stats_col2:
                st.markdown(f"""
                <div class="metric-card">
                    <strong>{total_words:,}</strong><br>
                    Total Words
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            sorted_transcriptions = sorted(transcriptions.items(), key=lambda x: int(x[0]), reverse=True)
            for counter, data in sorted_transcriptions:
                # Create a more compact and styled expander
                duration = data.get('duration_seconds', 0)
                duration_str = f"{duration:.1f}s" if duration else "N/A"
                language_flag = "🇺🇸" if data.get('language') == 'en-US' else "🇮🇳" if data.get('language') in ['hi-IN', 'en-IN'] else "🌐"
                
                with st.expander(f"📝 #{counter} • {data['timestamp'][:10]} • {language_flag} {data.get('language', 'Unknown')}"):
                    # Session details
                    detail_col1, detail_col2 = st.columns(2)
                    with detail_col1:
                        st.markdown(f"**⏱️ Duration:** {duration_str}")
                        st.markdown(f"**📊 Words:** {data['word_count']}")
                    with detail_col2:
                        st.markdown(f"**🕐 Time:** {data['timestamp'][11:]}")
                        st.markdown(f"**🌐 Language:** {data.get('language', 'Unknown')}")
                    
                    # Transcript preview
                    transcript_text = "\n".join(data['session_transcript'])
                    if len(transcript_text) > 200:
                        preview_text = transcript_text[:200] + "..."
                        st.markdown(f"**Preview:** {preview_text}")
                        
                        if st.button(f"👁️ View Full Transcript", key=f"view_full_{counter}"):
                            st.text_area("Full Transcript", transcript_text, height=150, key=f"full_transcript_{counter}")
                    else:
                        st.text_area("Transcript", transcript_text, height=100, key=f"transcript_{counter}")
                    
                    # Action buttons for each transcription
                    action_col1, action_col2 = st.columns(2)
                    with action_col1:
                        if st.button(f"🏥 Generate Report", key=f"gen_report_{counter}"):
                            with st.spinner("Generating report..."):
                                report = generate_medical_report(transcript_text)
                                if report:
                                    st.success("Report generated!")
                                    st.markdown("**Generated Report:**")
                                    st.markdown(report)
                                else:
                                    st.error("Failed to generate report")
                    
                    with action_col2:
                        if transcript_text and st.button(f"📄 Download PDF", key=f"download_{counter}"):
                            with st.spinner("Creating PDF..."):
                                pdf_data = create_pdf_report(None, transcript_text, counter)
                                if pdf_data:
                                    filename = f"transcript_{counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                    st.download_button(
                                        label="📥 Download",
                                        data=pdf_data,
                                        file_name=filename,
                                        mime="application/pdf",
                                        key=f"dl_btn_{counter}"
                                    )
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #6c757d;">
                <h4>📭 No Previous Transcriptions</h4>
                <p>Start recording to create your first medical transcription!</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Update transcription display for live recording
    if st.session_state.is_recording:
        try:
            # Process any new transcription updates
            updates_processed = 0
            while updates_processed < 10:  # Limit to prevent infinite loop
                try:
                    status, text = st.session_state.transcriber.transcript_queue.get_nowait()
                    if status == "final":
                        # Final transcript is already added to current_session in the transcriber
                        pass
                    updates_processed += 1
                except queue.Empty:
                    break
            
            # Refresh the display every few seconds during recording
            time.sleep(0.5)
            st.experimental_rerun()
        except Exception as e:
            print(f"Error updating display: {str(e)}")  # Debug print

if __name__ == "__main__":
    main() 