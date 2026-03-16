from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rapidfuzz import process, fuzz
import json
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Load the database once on startup
with open('services.json', 'r') as f:
    services_db = json.load(f)

# 2. Build a smarter search space using a dictionary mapping.
# Key: Service ID | Value: A mega-string of all searchable text for that service.
search_dict = {}
for service in services_db:
    # We combine name, category, description, and tags into one massive block of context
    combined_text = f"{service['name']} {service['category']} {service['description']} {' '.join(service['tags'])}"
    search_dict[service['id']] = combined_text

@app.get("/chat")
async def chat_bot(query: str):
    query = query.lower()
    
    # Logging feature
    with open("chat_logs.txt", "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] User Asked: {query}\n")

    # --- 3. THE INTENT INTERCEPTOR ---
    # Hardcoded routing layer to catch explicit web requests before RapidFuzz guesses
    update_keywords = ["update", "old", "legacy", "fix", "redesign", "overhaul"]
    build_keywords = ["scratch", "new", "build", "create", "make me a"]

    # Check for legacy update intent
    if any(word in query for word in update_keywords) and ("site" in query or "website" in query):
        matched_id = "svc_002"
        for service in services_db:
            if service['id'] == matched_id:
                return {
                    "response": f"I think you're looking for our <strong>{service['name']}</strong> package (${service['price']}). {service['description']}",
                    "match": True
                }

    # Check for new build intent
    elif any(word in query for word in build_keywords) and ("site" in query or "website" in query or "app" in query):
        matched_id = "svc_010"
        for service in services_db:
            if service['id'] == matched_id:
                return {
                    "response": f"I think you're looking for our <strong>{service['name']}</strong> package (${service['price']}). {service['description']}",
                    "match": True
                }
    # ---------------------------------

    # 4. RapidFuzz searches the dictionary values if no explicit intent is triggered. 
    # It returns a tuple: (matched_string, score, dictionary_key)
    best_match = process.extractOne(query, search_dict, scorer=fuzz.WRatio)
    
    if best_match and best_match[1] > 70:
        matched_id = best_match[2] # This extracts the service['id'] we assigned as the key
        
        # Find the exact service using its unique ID instead of guessing by text
        for service in services_db:
            if service['id'] == matched_id:
                return {
                    "response": f"I think you're looking for our <strong>{service['name']}</strong> package (${service['price']}). {service['description']}",
                    "match": True
                }
    
    # Fallback response if no confident match is found
    return {
        "response": 'I\'m not exactly sure what you need, but I can definitely help! Why don\'t you fill out the <strong><a href="#" onclick="openModal(); return false;" style="color: #415a77;">Contact Form</a></strong> for a custom quote?',
        "match": False
    }

if __name__ == "__main__":
    import uvicorn
    # Keeping this set up for local testing; Render will override this in production
    uvicorn.run(app, host="127.0.0.1", port=8000)
