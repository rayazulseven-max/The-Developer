import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rapidfuzz import process, fuzz
import json
import datetime
import re  

from google import genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open('services.json', 'r') as f:
    services_db = json.load(f)

with open('hcpcs.json', 'r') as f:
    hcpcs_db = json.load(f)

# ==========================================
# 1. FOOLPROOF LIST-BASED SEARCH SPACES
# ==========================================
services_search_list = []
for service in services_db:
    combined_text = f"{service['name']} {service['category']} {service['description']} {' '.join(service.get('tags', []))}"
    services_search_list.append(combined_text)

# UPDATED: Clean text, no more repeating words!
hcpcs_search_list = []
for item in hcpcs_db:
    tags = " ".join(item.get('tags', []))
    clean_text = f"{item['code']} {item['description']} {tags}"
    hcpcs_search_list.append(clean_text)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# ==========================================
# 🧠 THE RAG GENERATOR FUNCTION 
# ==========================================
async def generate_rag_response(user_query: str, retrieved_service: dict = None):
    if retrieved_service:
        context = f"""
        SERVICE FOUND IN DATABASE:
        Name: {retrieved_service['name']}
        Category: {retrieved_service['category']}
        Price: ${retrieved_service['price']}
        Details: {retrieved_service['description']}
        """
    else:
        context = "No specific service found in the database."

    system_prompt = f"""
    You are Azul-Bot, the professional sales agent for Ray Azul Perez.
    The user asked: "{user_query}"
    
    Here is the most relevant service retrieved from our database:
    {context}
    
    INSTRUCTIONS:
    1. First, decide if the retrieved service actually relates to what the user is asking.
    2. If it DOES match: Answer naturally using ONLY the facts above. Format the service name in bold HTML tags (e.g., <strong>Name</strong>).
    3. If it DOES NOT match: Politely say you don't see a specific package for that, and suggest they fill out the Contact Form for a custom quote.
    4. Keep the response under 3 sentences. Do NOT use markdown outside of the requested HTML tags.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt
        )
        return response.text
    except Exception as e:
        return f"<strong>Gemini Error:</strong> {str(e)}"

# ==========================================
# 3. THE DUAL-ROUTING ENDPOINT
# ==========================================
@app.get("/chat")
async def chat_bot(query: str, context: str = "portfolio"):
    query_lower = query.lower()
    
    with open("chat_logs.txt", "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] Context: [{context.upper()}] | User Asked: {query}\n")

    if context == "medical":
        exact_code_pattern = r"^[a-zA-Z]\d{4}$"
        if re.match(exact_code_pattern, query.strip()):
            matched_code = query.strip().upper()
            for item in hcpcs_db:
                if item['code'] == matched_code:
                    price = f"${item['price_estimate']:.2f}" if item['price_estimate'] > 0 else "Pricing Varies"
                    return {"response": f"<strong>{item['code']}</strong> ({item['category']}): {item['description']} <br><strong>Est. Cost: {price}</strong>", "match": True}
        
        # UPDATED: LIST BASED MEDICAL SEARCH using token_set_ratio
        best_match = process.extractOne(query_lower, hcpcs_search_list, scorer=fuzz.token_set_ratio)
        if best_match and best_match[1] > 65:
            match_index = best_match[2] 
            item = hcpcs_db[match_index]
            price = f"${item['price_estimate']:.2f}" if item['price_estimate'] > 0 else "Pricing Varies"
            return {"response": f"Clinical Match Found: <strong>{item['code']}</strong> ({item['category']}). {item['description']} <br><strong>Est. Cost: {price}</strong>", "match": True}
        
        return {"response": "I couldn't find a direct clinical match. Please verify the supply name, drug, or HCPCS code.", "match": False}

    else:
        update_keywords = ["update", "old", "legacy", "fix", "redesign", "overhaul"]
        build_keywords = ["scratch", "new", "build", "create", "make me a"]

        if any(word in query_lower for word in update_keywords) and ("site" in query_lower or "website" in query_lower):
            for service in services_db:
                if service['id'] == "svc_002":
                    rag_reply = await generate_rag_response(query, service)
                    return {"response": rag_reply, "match": True}

        elif any(word in query_lower for word in build_keywords) and ("site" in query_lower or "website" in query_lower or "app" in query_lower):
            for service in services_db:
                if service['id'] == "svc_010":
                    rag_reply = await generate_rag_response(query, service)
                    return {"response": rag_reply, "match": True}

        # 2. LIST BASED PORTFOLIO SEARCH (True RAG Architecture)
        best_match = process.extractOne(query_lower, services_search_list, scorer=fuzz.token_set_ratio)
        
        if best_match:
            match_index = best_match[2] 
            matched_service = services_db[match_index]
            rag_reply = await generate_rag_response(query, matched_service)
            return {"response": rag_reply, "match": True}
            
        rag_reply = await generate_rag_response(query, None)
        return {"response": rag_reply, "match": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
