import sys
import os

print("Verifying Imports...")
try:
    import openai
    print("openai imported")
except ImportError as e:
    print(f"openai failed: {e}")

try:
    import pytz
    print("pytz imported")
except ImportError as e:
    print(f"pytz failed: {e}")

try:
    from agents.astrologer import AstrologerAgent
    print("AstrologerAgent imported")
except ImportError as e:
    print(f"AstrologerAgent failed: {e}")

try:
    from agents.director import DirectorAgent
    print("DirectorAgent imported")
except ImportError as e:
    print(f"DirectorAgent failed: {e}")

try:
    from agents.uploader import YouTubeUploader
    print("YouTubeUploader imported")
except ImportError as e:
    print(f"YouTubeUploader failed: {e}")

try:
    from editor import EditorEngine
    print("EditorEngine imported")
except ImportError as e:
    print(f"EditorEngine failed: {e}")

print("Verification Complete")
