import requests
import json
import time

# Your Vapi API key
API_KEY = '26b90483-ca41-4230-b6ba-9c72003e6baf'

# Headers for API request
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# Simple assistant configuration with Deepgram transcription
assistant = {
    'firstMessage': (
        "Hello, this is your coding assistant calling. "
        "I need a quick clarification: Should the API support social login like Google and Facebook, "
        "or just email and password authentication? Please give me a clear answer."
    ),
    'model': {
        'provider': 'openai',
        'model': 'gpt-4o',
        'temperature': 0.7,
        'messages': [
            {
                'role': 'system',
                'content': (
                    "You are a professional coding assistant gathering requirements. "
                    "Ask the clarification question clearly. When the user responds, "
                    "summarize their decision and thank them and say talk to you later, then end the call. "
                    "make sure the user actualyl finished giving their clarification before you end the call."
                    "Be sure to explain to the user as succincly as possible so the developer can understand what all the options are and make an informed decision."
                )
            }
        ],
        'tools': [
            {
                'type': 'endCall'
            }
        ]
    },
    'voice': {
        'provider': '11labs',
        'voiceId': 'pNInz6obpgDQGcFmaJgB'  # Adam - masculine voice
    },
    'transcriber': {
        'provider': 'deepgram',
        'model': 'nova-2',
        'language': 'en-US'
    },
    'firstMessageMode': 'assistant-speaks-first',
    'silenceTimeoutSeconds': 10,
    'maxDurationSeconds': 90
}

# Call payload
call_payload = {
    'assistant': assistant,
    'customer': {
        'number': '+16508856407'
    },
    'phoneNumberId': 'd5a026d4-b76e-41a6-b04d-92c1357072b2'
}

print("🚀 Making call with improved transcription...")
response = requests.post('https://api.vapi.ai/call', headers=headers, json=call_payload)

if response.status_code == 201:
    call_data = response.json()
    call_id = call_data.get('id')
    print(f"✅ Call initiated! Call ID: {call_id}")
    print("📞 Answer your phone...")
    
    # Wait for call to complete and get results
    print("⏳ Waiting for call to complete...")
    
    while True:
        time.sleep(5)  # Check every 5 seconds
        
        # Get call details
        call_response = requests.get(f'https://api.vapi.ai/call/{call_id}', headers=headers)
        
        if call_response.status_code == 200:
            call_info = call_response.json()
            status = call_info.get('status')
            
            print(f"📊 Call status: {status}")
            
            if status == 'ended':
                # Call finished - get the transcript
                print("\n🏁 CALL COMPLETED!")
                print("=" * 50)
                
                # Get conversation messages
                artifact = call_info.get('artifact', {})
                messages = artifact.get('messages', [])
                
                print("💬 CONVERSATION SUMMARY:")
                user_responses = []
                bot_responses = []
                
                for msg in messages:
                    if msg.get('role') == 'user':
                        user_msg = msg.get('message', '')
                        if user_msg:
                            user_responses.append(user_msg)
                            print(f"   👤 You said: \"{user_msg}\"")
                    elif msg.get('role') == 'bot':
                        bot_msg = msg.get('message', '')
                        if bot_msg:
                            bot_responses.append(bot_msg)
                            print(f"   🤖 Assistant: \"{bot_msg}\"")
                
                # Save the decision to a simple file
                if user_responses:
                    decision = " | ".join(user_responses)  # Join multiple responses
                    
                    # Create a cleaner summary
                    summary = "Email and password only"
                    if any(word in decision.lower() for word in ['google', 'facebook', 'social', 'oauth']):
                        if 'google' in decision.lower() and 'facebook' not in decision.lower():
                            summary = "Google social login only"
                        elif 'facebook' in decision.lower() and 'google' not in decision.lower():
                            summary = "Facebook social login only"
                        elif 'google' in decision.lower() and 'facebook' in decision.lower():
                            summary = "Google and Facebook social login"
                        else:
                            summary = "Social login (unspecified provider)"
                    
                    with open('clarification_decision.txt', 'w') as f:
                        f.write(f"Clarification Decision\n")
                        f.write(f"=====================\n")
                        f.write(f"Question: Social login support?\n")
                        f.write(f"Raw Response: {decision}\n")
                        f.write(f"Interpreted Decision: {summary}\n")
                        f.write(f"Call ID: {call_id}\n")
                        f.write(f"\nFull Conversation:\n")
                        for i, (user, bot) in enumerate(zip(user_responses, bot_responses), 1):
                            f.write(f"{i}. You: {user}\n")
                            f.write(f"{i}. Assistant: {bot}\n")
                    
                    print(f"\n🎯 RAW RESPONSE: \"{decision}\"")
                    print(f"🧠 INTERPRETED DECISION: {summary}")
                    print(f"💾 Saved to: clarification_decision.txt")
                else:
                    print("❌ No clear response captured")
                
                break
        else:
            print(f"❌ Error checking call status: {call_response.status_code}")
            break

else:
    print(f"❌ Failed to initiate call: {response.status_code}")
    print(f"Response: {response.text}")