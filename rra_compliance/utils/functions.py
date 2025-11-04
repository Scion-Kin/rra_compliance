import base64
import hashlib
import re

def shorten_string(input_string, length=20):
	"""Shortens a string to the specified length."""
	sha = hashlib.sha256(input_string.encode()).digest()
	base = base64.urlsafe_b64encode(sha).decode('utf-8')
	base = re.sub(r'[^a-zA-Z0-9]', '', base)
	return base[:length]
