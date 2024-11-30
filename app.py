from flask import Flask, request, jsonify
from flask_sock import Sock
from twilio.twiml.voice_response import VoiceResponse, Start
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import vosk
from pyngrok import ngrok
from threading import Lock
import json
import base64
import audioop
import os
from dotenv import load_dotenv
from ai_agent import AIAgent
import time

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
sock = Sock(app)

# Initialize Vosk model
model = vosk.Model('model')

# Active calls tracking
active_calls = {}
active_calls_lock = Lock()

# Load Twilio credentials
twilio_client = Client(
    os.environ['TWILIO_ACCOUNT_SID'],
    os.environ['TWILIO_AUTH_TOKEN']
)

@app.route('/outgoing_call', methods=['POST'])
def outgoing_call():
    call_sid = request.form.get('CallSid')
    print(f"\n=== Starting call {call_sid} ===")
    
    # Get machine detection results from Twilio
    answered_by = request.form.get('AnsweredBy')
    print(f"Twilio Machine Detection: {answered_by}")
    
    with active_calls_lock:
        active_calls[call_sid] = {
            'transcript': '',
            'state': 'initializing',
            'twilio_detection': answered_by,
            'ai_detection': None,
            'dtmf_options_detected': [],
            'background_type': None,
            'start_time': time.time()
        }
    
    response = VoiceResponse()
    
    # Enable media streams
    start = Start()
    start.stream(url=f'wss://{request.host}/stream/{call_sid}')
    response.append(start)
    
    # Add initial pause to allow stream to connect
    response.pause(length=1)
    
    print(f"TwiML Response: {str(response)}")
    return str(response)

@sock.route('/stream/<call_sid>')
async def stream(ws, call_sid):
    print(f'\n=== Starting stream for call {call_sid} ===')
    
    try:
        # Initialize Vosk recognizer
        rec = vosk.KaldiRecognizer(model, 16000)
        agent = AIAgent(goal="Detect call environment and menu options")
        
        print('Transcription started...')
        last_activity = time.time()
        silence_threshold = 3  # seconds
        
        while True:
            try:
                message = await ws.receive()
                packet = json.loads(message)
                
                if packet['event'] == 'media':
                    # Process audio
                    audio = base64.b64decode(packet['media']['payload'])
                    audio = audioop.ulaw2lin(audio, 2)
                    audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
                    
                    # Get transcription
                    if rec.AcceptWaveform(audio):
                        result = json.loads(rec.Result())
                        text = result.get('text', '').strip()
                        
                        if text:
                            print(f"\nTranscript: {text}")
                            last_activity = time.time()
                            
                            # Store transcript
                            with active_calls_lock:
                                if call_sid in active_calls:
                                    active_calls[call_sid]['transcript'] += f"{text} "
                            
                            # Analyze with AI
                            analysis = agent.analyze_text(text)
                            if analysis:
                                print(f"\nAI Analysis:")
                                print(f"Text Type: {analysis.get('text_type', 'unknown')}")
                                print(f"DTMF Action: {analysis.get('dtmf_action')}")
                                print(f"Transfer: {analysis.get('transfer')}")
                                print(f"State: {analysis.get('new_state')}")
                                
                                # Update call state
                                with active_calls_lock:
                                    if call_sid in active_calls:
                                        call_info = active_calls[call_sid]
                                        call_info['ai_detection'] = analysis.get('text_type')
                                        call_info['background_type'] = analysis.get('text_type')
                                        
                                        # Store detected DTMF options
                                        if analysis.get('dtmf_action'):
                                            if analysis['dtmf_action'] not in call_info['dtmf_options_detected']:
                                                call_info['dtmf_options_detected'].append(analysis['dtmf_action'])
                                                print(f"\nDTMF Option Detected: {analysis['dtmf_action']}")
                    
                    else:
                        # Show partial results
                        partial = json.loads(rec.PartialResult())
                        if partial.get('partial', '').strip():
                            print(f"Partial: {partial['partial']}", end='\r')
                    
                    # Check for silence
                    if time.time() - last_activity > silence_threshold:
                        print("\nSilence detected...")
                        agent.update_silence(silence_threshold)
                
                elif packet['event'] == 'stop':
                    print(f"\nStream stopped for call {call_sid}")
                    break
                    
            except Exception as e:
                print(f"Error processing stream: {str(e)}")
                break
                
    except Exception as e:
        print(f"Stream error: {str(e)}")
    finally:
        # Print final analysis
        with active_calls_lock:
            if call_sid in active_calls:
                call_info = active_calls[call_sid]
                duration = time.time() - call_info['start_time']
                print(f"\n=== Call Analysis for {call_sid} ===")
                print(f"Duration: {duration:.2f} seconds")
                print(f"Twilio Machine Detection: {call_info['twilio_detection']}")
                print(f"AI Detection: {call_info['ai_detection']}")
                print(f"Background Type: {call_info['background_type']}")
                print(f"DTMF Options Detected: {call_info['dtmf_options_detected']}")
                print(f"Final Transcript: {call_info['transcript']}")
        
        print(f"\n=== Stream ended for call {call_sid} ===")

if __name__ == '__main__':
    # Start ngrok
    port = 3001
    public_url = ngrok.connect(port, bind_tls=True).public_url
    print(f'\nNgrok URL: {public_url}')
    
    # Start Flask app
    app.run(port=port, debug=True)
