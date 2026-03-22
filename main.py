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

# We only need RapidFuzz lists for the massive Medical Database now!
hcpcs_search_list = []
for item in hcpcs_db:
    tags = " ".join(item.get('tags', []))
    clean_text = f"{item['code']} {item['description']} {tags}"
    hcpcs_search_list.append(clean_text)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


# ==========================================
# 3. THE DUAL-ROUTING ENDPOINT
# ==========================================
@app.get("/chat")
async def chat_bot(query: str, context: str = "portfolio"):
    query_lower = query.lower()
    
    with open("chat_logs.txt", "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] Context: [{context.upper()}] | User Asked: {query}\n")

    # ==========================================
    # ROUTE A: CLINICAL (RapidFuzz + Strict Matching)
    # ==========================================
    if context == "medical":
        exact_code_pattern = r"^[a-zA-Z]\d{4}$"
        if re.match(exact_code_pattern, query.strip()):
            matched_code = query.strip().upper()
            for item in hcpcs_db:
                if item['code'] == matched_code:
                    price = f"${item['price_estimate']:.2f}" if item['price_estimate'] > 0 else "Pricing Varies"
                    return {"response": f"<strong>{item['code']}</strong> ({item['category']}): {item['description']} <br><strong>Est. Cost: {price}</strong>", "match": True}
        
        best_match = process.extractOne(query_lower, hcpcs_search_list, scorer=fuzz.token_set_ratio)
        if best_match and best_match[1] > 65:
            match_index = best_match[2] 
            item = hcpcs_db[match_index]
            price = f"${item['price_estimate']:.2f}" if item['price_estimate'] > 0 else "Pricing Varies"
            return {"response": f"Clinical Match Found: <strong>{item['code']}</strong> ({item['category']}). {item['description']} <br><strong>Est. Cost: {price}</strong>", "match": True}
        
        return {"response": "I couldn't find a direct clinical match. Please verify the supply name, drug, or HCPCS code.", "match": False}


    # ==========================================
    # ROUTE B: PORTFOLIO (Full Gemini 2.5 Brain)
    # ==========================================
    else:
        # We hand Gemini the ENTIRE menu and let it do the routing natively
        portfolio_context = json.dumps(services_db)

        system_prompt = f"""
        You are Azul-Bot, the professional sales agent for Ray Azul Perez.
        The user asked: "{query}"
        
        Here is Ray's ENTIRE list of available services:
        {portfolio_context}
        
        INSTRUCTIONS:
        1. Find the best matching service. Understand typos (like "customer" vs "custom").
        2. If you find a match: Answer naturally, state the price, and bold the <strong>Name</strong>.
        3. If NO service matches: Politely suggest they fill out the Contact Form.
        4. CONTACT LINK: Always wrap "Contact Form" in: 
           <a href="#" onclick="openModal(); return false;" style="color: #415a77; text-decoration: underline; font-weight: bold;">Contact Form</a>
        5. ORDER LINK: If a match is found, add a second link that says "Order [Name] Now" using:
           <a href="#" onclick="openOrderModal('[Name]'); return false;" style="color: #2e7d32; text-decoration: underline; font-weight: bold; margin-left: 10px;">Order [Name] Now</a>
        6. Keep the response under 3 sentences. Do NOT use markdown outside of HTML tags.
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=system_prompt
            )
            return {"response": response.text, "match": True}
        except Exception as e:
            return {"response": f"<strong>Gemini Error:</strong> {str(e)}", "match": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
