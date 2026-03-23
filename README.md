# Ray Azul Perez | Interactive AI Portfolio & Dual-Route RAG Architecture

## **[🚀 View Live Demo Here](https://rayazulseven-max.github.io/The-Developer/)**

This repository contains the source code for my interactive portfolio and suite of AI-driven web applications. It demonstrates full-stack development, combining responsive, framework-agnostic frontend engineering with a high-throughput FastAPI backend. 

The core feature of this platform is a **Dual-Route Retrieval-Augmented Generation (RAG) pipeline** powered by Google's Gemini 2.5 Flash model.

## 🧠 System Architecture & Telemetry

The backend operates on a context-aware routing protocol. Depending on the endpoint called by the frontend UI, the API dynamically swaps its JSON vector approximations, system instructions, and LLM persona. 

**Observability:** The system includes built-in telemetry, persistently writing user queries and context triggers to a local audit log. This creates a data trail for gap analysis, allowing for continuous iteration of the product catalog and prompt engineering based on real-world user intent.

## 🛡️ Key Engineering Highlights

### 1. Strict Context-Grounding (Zero Hallucination)
In medical and enterprise environments, AI hallucinations carry significant liability. This system utilizes strict system prompts to constrain the LLM exclusively to the provided JSON arrays. If a user asks the Clinical Bot about Medicaid coverage or the Sales Bot for a rocket ship, the system is programmed to explicitly refuse the out-of-domain query and trigger a fallback lead-generation funnel.

### 2. Stateful Conversational Memory
The application upgrades standard stateless REST APIs by maintaining a rolling, asynchronous chat-history array on the client side. This payload is passed via `POST` request to the backend, enabling the AI to maintain context, understand compound queries, and process conversational follow-ups seamlessly across multiple turns.

### 3. Dynamic UI Integration
The AI operates beyond simple text generation; it acts as a functional UI navigator. The backend is instructed to output specific HTML anchor tags embedded with JavaScript triggers. This allows the AI to proactively open modals and auto-fill forms for the user, bridging the gap between conversational AI and traditional e-commerce funnels.

## 📂 Project Suite Overview

* **Automated Sales Agent (`services.html`):** An interactive e-commerce environment featuring a modular JSON database parsed by an intelligent RAG chatbot for dynamic service quoting and lead capture.
* **Clinical Search Engine (`hcpcs.html`):** Grounded in AAPC professional coding standards, this tool parses HCPCS Level II codes and maps descriptive lay-terms. It utilizes a strict confidence threshold for semantic matches to ensure clinical data integrity.
* **Dynamic Media Catalog (`music.html`):** A responsive, data-driven web application featuring custom JSON parsing, multi-select algorithmic filtering, and an integrated audio playback architecture.
* **Command Override System (`index.html`):** Features a hidden, passkey-protected admin modal connected to a RESTful endpoint for real-time CRUD operations on community feedback.

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI, Pydantic, Uvicorn (Optimized for asynchronous request handling)
* **AI/LLM:** Google GenAI SDK (`gemini-2.5-flash`)
* **Frontend:** Zero-dependency Native JavaScript (ES6+), HTML5, CSS3 (Architected for sub-second latency and cross-device responsiveness)
* **Deployment:** Render (Backend API), GitHub Pages (Frontend Edge Delivery)
* **Data Layer:** JSON Document Stores, REST API Integration



## **Author**: Ray Azul Perez | AI Developer • Data Analyst • UI Engineer
