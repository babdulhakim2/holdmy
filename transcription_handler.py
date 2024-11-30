import json
import base64
import audioop
import vosk
from datetime import datetime
from queue import Queue
import os
import re

class VoskTranscriptionHandler:
    def __init__(self, model_path='model', call_sid=None):
        if not os.path.exists(model_path):
            raise ValueError(f"Vosk model not found at {model_path}. Please download it first.")
        
        self.model = vosk.Model(model_path)
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        self.call_sid = call_sid
        self.monitor_clients = set()
        self.call_status = {
            'state': 'initializing',
            'last_activity': datetime.now().isoformat(),
            'dtmf_history': [],
            'transcription': [],
            'machine_detection': None
        }
        
    async def broadcast_update(self, update_type, data):
        message = {
            'type': update_type,
            'timestamp': datetime.now().isoformat(),
            'call_sid': self.call_sid,
            'data': data
        }
        print(f"Broadcasting: {message}")
        for client in self.monitor_clients:
            try:
                await client.send(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                self.monitor_clients.remove(client)
        
    async def handle_audio_stream(self, websocket):
        print(f"\nStarting audio stream for call {self.call_sid}")
        self.call_status['state'] = 'streaming'
        await self.broadcast_update('status', self.call_status)
        
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data['event'] == 'media':
                    # Process audio
                    audio = base64.b64decode(data['media']['payload'])
                    audio = audioop.ulaw2lin(audio, 2)
                    audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
                    
                    if self.recognizer.AcceptWaveform(audio):
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '').strip()
                        
                        if text:
                            print(f"\nTranscription: {text}")
                            self.call_status['transcription'].append({
                                'timestamp': datetime.now().isoformat(),
                                'text': text
                            })
                            await self.broadcast_update('transcription', {'text': text})
                            
                            # Check for menu options
                            if any(keyword in text.lower() for keyword in ['press', 'dial', 'option', 'menu']):
                                print("Detected menu prompt")
                                await self.broadcast_update('menu_detected', {'text': text})
                                
                                # Extract DTMF options
                                numbers = re.findall(r'press (\d+)|dial (\d+)', text.lower())
                                if numbers:
                                    dtmf_options = [num for group in numbers for num in group if num]
                                    await self.broadcast_update('dtmf_options', {
                                        'options': dtmf_options,
                                        'text': text
                                    })

                elif data['event'] == 'mark':
                    # Handle markers (like DTMF)
                    if 'dtmf' in data:
                        dtmf = data['dtmf']
                        print(f"DTMF detected: {dtmf}")
                        self.call_status['dtmf_history'].append({
                            'timestamp': datetime.now().isoformat(),
                            'digit': dtmf
                        })
                        await self.broadcast_update('dtmf', {'digit': dtmf})

        except Exception as e:
            print(f"Error in audio stream: {e}")
            self.call_status['state'] = 'error'
            await self.broadcast_update('error', {'error': str(e)})
            raise