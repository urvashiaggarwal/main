import google.generativeai as genai

# 🔑 Paste your API key here directly
genai.configure(api_key="AIzaSyAveAkSIHnSapRoB3V2SB65lzup8BxOgDU")

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

# 🔁 Example prompt
response = model.generate_content("What is the capital of France?")
print(response.text)
