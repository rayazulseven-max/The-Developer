from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rapidfuzz import process, fuzz
import json
import datetime
import re  # Added for Clinical Code Regex Matching

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Load BOTH databases once on startup
with open('services.json', 'r') as f:
    services_db = json.load(f)

with open('hcpcs.json', 'r') as f:
    hcpcs_db = json.load(f)


# 2. Build Isolated Search Spaces
# PORTFOLIO DICTIONARY
services_search_dict = {}
for service in services_db:
    combined_text = f"{service['name']} {service['category']} {service['description']} {' '.join(service['tags'])}"
    services_search_dict[service['id']] = combined_text

# MEDICAL DICTIONARY
hcpcs_search_dict = {}
for item in hcpcs_db:
    tags = " ".join(item.get('tags', []))
    combined_text = f"{item['code']} {item['category']} {item['description']} {tags}"
    hcpcs_search_dict[item['code']] = combined_text


# 3. The Dual-Routing Endpoint
# Added 'context' parameter to determine which brain to use (defaults to portfolio so your old site doesn't break)
@app.get("/chat")
async def chat_bot(query: str, context: str = "portfolio"):
    query_lower = query.lower()
    
    # Logging feature (Now tracks which context was used)
    with open("chat_logs.txt", "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] Context: [{context.upper()}] | User Asked: {query}\n")


    # ==========================================
    # ROUTE A: THE CLINICAL INTELLIGENCE ENGINE
    # ==========================================
    if context == "medical":
        
        # A1. The Clinical Interceptor (Zero-Latency Exact Match)
        # Checks if query is exactly 1 letter followed by 4 digits (e.g., E0143, J1745)
        exact_code_pattern = r"^[a-zA-Z]\d{4}$"
        if re.match(exact_code_pattern, query.strip()):
            matched_code = query.strip().upper()
            for item in hcpcs_db:
                if item['code'] == matched_code:
                    price = f"${item['price_estimate']:.2f}" if item['price_estimate'] > 0 else "Pricing Varies"
                    return {
                        "response": f"<strong>{item['code']}</strong> ({item['category']}): {item['description']} <br><strong>Est. Cost: {price}</strong>",
                        "match": True
                    }
        
        # A2. Clinical Fuzzy Matcher (For plain English searches)
        best_match = process.extractOne(query_lower, hcpcs_search_dict, scorer=fuzz.WRatio)
        
        # INCREASED THRESHOLD: Raised from 65 to 80 to prevent aggressive hallucinations 
        if best_match and best_match[1] > 80:
            matched_code = best_match[2] # Extracts the HCPCS Code we assigned as the key
            for item in hcpcs_db:
                if item['code'] == matched_code:
                    price = f"${item['price_estimate']:.2f}" if item['price_estimate'] > 0 else "Pricing Varies"
                    return {
                        "response": f"Clinical Match Found: <strong>{item['code']}</strong> ({item['category']}). {item['description']} <br><strong>Est. Cost: {price}</strong>",
                        "match": True
                    }
        
        # A3. Medical Fallback (Will trigger much more often now if the query isn't a solid match)
        return {
            "response": "I couldn't find a direct clinical match. Please verify the supply name, drug, or HCPCS code.",
            "match": False
        }


    # ==========================================
    # ROUTE B: THE PORTFOLIO SALES AGENT
    # ==========================================
    else:
        # B1. The Intent Interceptor
        update_keywords = ["update", "old", "legacy", "fix", "redesign", "overhaul"]
        build_keywords = ["scratch", "new", "build", "create", "make me a"]

        if any(word in query_lower for word in update_keywords) and ("site" in query_lower or "website" in query_lower):
            matched_id = "svc_002"
            for service in services_db:
                if service['id'] == matched_id:
                    return {
                        "response": f"I think you're looking for our <strong>{service['name']}</strong> package (${service['price']}). {service['description']}",
                        "match": True
                    }

        elif any(word in query_lower for word in build_keywords) and ("site" in query_lower or "website" in query_lower or "app" in query_lower):
            matched_id = "svc_010"
            for service in services_db:
                if service['id'] == matched_id:
                    return {
                        "response": f"I think you're looking for our <strong>{service['name']}</strong> package (${service['price']}). {service['description']}",
                        "match": True
                    }

        # B2. RapidFuzz Search
        best_match = process.extractOne(query_lower, services_search_dict, scorer=fuzz.WRatio)
        
        if best_match and best_match[1] > 70:
            matched_id = best_match[2] 
            for service in services_db:
                if service['id'] == matched_id:
                    return {
                        "response": f"I think you're looking for our <strong>{service['name']}</strong> package (${service['price']}). {service['description']}",
                        "match": True
                    }
        
        # B3. Portfolio Fallback
        return {
            "response": 'I\'m not exactly sure what you need, but I can definitely help! Why don\'t you fill out the <strong><a href="#" onclick="openModal(); return false;" style="color: #415a77;">Contact Form</a></strong> for a custom quote?',
            "match": False
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
