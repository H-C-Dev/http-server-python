# HTTP/1.1 Backend Framework

A custom HTTP/1.1 Python framework built entirely from scratch without ASGI/httptools or external dependencies.  
Designed to explore low-level protocol design, performance, security, and observability.

## Tech Stack
- Python

## Key Features
- Custom request parser  
- DX-friendly middleware layer  
- Concurrency via threads and processes  
- Production-grade observability: structured JSON logs, trace IDs, latency metrics, slow-request tracing  
- Security and developer-focused features: CORS, CSRF (HttpOnly cookies), schema validation, Redis caching, session handling, rate limiting, type-safe support  

## Examples
### Full-Stack Web App (Starling API)
An example project built on this framework to demonstrate its flexibility in financial applications.  

**Stack:** Next.js, Custom Python Framework, AWS SNS, Starling Bank API  

**Features:**
- Securely fetched account balances via the Starling Bank API  
- Automated daily balance email notifications using AWS SNS  
- Security-first backend with a custom outbound HTTP client and secure authentication  

**Focus:**  
Showcases strong interest in financial systems and regulatory technology while applying security and cloud automation on top of the custom backend.
