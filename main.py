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

with open('services.json', 'r') as f:
    services_db = json.load(f)

search_space = []
for s in services_db:
    search_space.append(s['name'])
    search_space.extend(s['tags'])

@app.get("/chat")
async def chat_bot(query: str):
    query = query.lower()
    
    # Logging feature
    with open("chat_logs.txt", "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] User Asked: {query}\n")

    best_match = process.extractOne(query, search_space, scorer=fuzz.WRatio)
    
    if best_match and best_match[1] > 70:
        matched_text = best_match[0]
        for service in services_db:
            if matched_text == service['name'] or matched_text in service['tags']:
                return {
                    "response": f"I think you're looking for our **{service['name']}** package (${service['price']}). {service['description']}",
                    "match": True
                }
    
    return {
        "response": "I'm not exactly sure what you need, but I can definitely help! Why don't you fill out the **Contact Form** for a custom quote?",
        "match": False
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
