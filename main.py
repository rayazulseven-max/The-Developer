import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rapidfuzz import process, fuzz
import json
import datetime
import re  

# 1. NEW SDK IMPORT
from google import genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load BOTH databases once on startup
with open('services.json', 'r') as f:
    services_db = json.load(f)

with open('hcpcs.json', 'r') as f:
    hcpcs_db = json.load(f)

# Build Isolated Search Spaces
services_search_dict = {}
for service in services_db:
    combined_text = f"{service['name']} {service['category']} {service['description']} {' '.join(service['tags'])}"
    services_search_dict[service['id']] = combined_text

hcpcs_search_dict = {}
for item in hcpcs_db:
    tags = " ".join(item.get('tags', []))
    weighted_text = f"{item['description']} {item['description']} {tags} {tags} {item['code']}"
    hcpcs_search_dict[item['code']] = weighted_text


# 2. NEW SDK CLIENT INITIALIZATION
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# ==========================================
# 🧠 THE RAG GENERATOR FUNCTION (GEMINI POWERED)
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
        context = "No specific service found in the database for this query."

    system_prompt = f"""
    You are Azul-Bot, the professional sales agent for Ray Azul Perez.
    The user asked: "{user_query}"
    
    Here is the factual data retrieved from your database:
    {context}
    
    INSTRUCTIONS:
    1. Answer the user's query naturally and conversationally using ONLY the facts above.
    2. Be concise, clinical, and helpful. 
    3. Format the service name in bold HTML tags (e.g., <strong>Name</strong>).
    4. If no service was found in the database, politely suggest they fill out the Contact Form for a custom quote.
    5. Keep the response under 3 sentences. Do NOT use markdown outside of the requested HTML tags.
    """
    
    try:
        # 3. NEW SDK GENERATION CALL
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt
        )
        return response.text
    except Exception as e:
        return f"<strong>Gemini Error:</strong> {str(e)}"


# 3. The Dual-Routing Endpoint
@app.get("/chat")
async def chat_bot(query: str, context: str = "portfolio"):
    query_lower = query.lower()
    
    with open("chat_logs.txt", "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] Context: [{context.upper()}] | User Asked: {query}\n")

    # ==========================================
    # ROUTE A: THE CLINICAL INTELLIGENCE ENGINE (Left untouched)
    # ==========================================
    if context == "medical":
        exact_code_pattern = r"^[a-zA-Z]\d{4}$"
        if re.match(exact_code_pattern, query.strip()):
            matched_code = query.strip().upper()
            for item in hcpcs_db:
                if item['code'] == matched_code:
                    price = f"${item['price_estimate']:.2f}" if item['price_estimate'] > 0 else "Pricing Varies"
                    return {"response": f"<strong>{item['code']}</strong> ({item['category']}): {item['description']} <br><strong>Est. Cost: {price}</strong>", "match": True}
        
        best_match = process.extractOne(query_lower, hcpcs_search_dict, scorer=fuzz.WRatio)
        if best_match and best_match[1] > 80:
            matched_code = best_match[2] 
            for item in hcpcs_db:
                if item['code'] == matched_code:
                    price = f"${item['price_estimate']:.2f}" if item['price_estimate'] > 0 else "Pricing Varies"
                    return {"response": f"Clinical Match Found: <strong>{item['code']}</strong> ({item['category']}). {item['description']} <br><strong>Est. Cost: {price}</strong>", "match": True}
        
        return {"response": "I couldn't find a direct clinical match. Please verify the supply name, drug, or HCPCS code.", "match": False}


    # ==========================================
    # ROUTE B: THE PORTFOLIO SALES AGENT (RAG INTEGRATED)
    # ==========================================
    else:
        update_keywords = ["update", "old", "legacy", "fix", "redesign", "overhaul"]
        build_keywords = ["scratch", "new", "build", "create", "make me a"]

        # B1. Intent Interceptor
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

        # B2. RapidFuzz Search
        best_match = process.extractOne(query_lower, services_search_dict, scorer=fuzz.token_set_ratio)
        
        if best_match and best_match[1] > 60:
            matched_id = best_match[2] 
            for service in services_db:
                if service['id'] == matched_id:
                    rag_reply = await generate_rag_response(query, service)
                    return {"response": rag_reply, "match": True}
            
        # B3. Fallback
        rag_reply = await generate_rag_response(query, None)
        return {"response": rag_reply, "match": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
