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

    # 3. RapidFuzz searches the dictionary values. 
    # It returns a tuple: (matched_string, score, dictionary_key)
    best_match = process.extractOne(query, search_dict, scorer=fuzz.WRatio)
    
    if best_match and best_match[1] > 70:
        matched_id = best_match[2] # This extracts the service['id'] we assigned as the key
        
        # 4. Find the exact service using its unique ID instead of guessing by text
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
    uvicorn.run(app, host="127.0.0.1", port=8000)
