from services.murf_service import list_voices

data = list_voices()
voices = data if isinstance(data, list) else data.get("voices", [])

print("Total voices:", len(voices))
if voices:
    print("Each voice has these fields:", list(voices[0].keys()))
print()

# Show only voices for the languages in our dropdown
wanted = ["hi-", "es-", "fr-", "de-"]

for voice in voices:
    locale = str(voice.get("locale", ""))
    if any(locale.lower().startswith(prefix) for prefix in wanted):
        print(voice.get("voiceId"), "|", locale, "|", voice.get("displayLanguage"), "|", voice.get("gender"))
        