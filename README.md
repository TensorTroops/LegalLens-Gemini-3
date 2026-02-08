# LegalLens

**LegalLens** is an AI-powered, privacy-focused assistant for legal document understanding and risk detection—designed for Indian law, official government dictionaries, and multilingual support. LegalLens lets anyone upload, scan, and explore legal contracts/agreements with instant insights, real-time alerts, robust security, and seamless cloud integration.

---

## Overview

LegalLens acts as your wise, multilingual legal companion, explaining complex legal documents, detecting and warning about risky clauses instantly, and turning contracts into clear, actionable knowledge. Built with a focus on real-world usability, inclusiveness, and bulletproof privacy.

---

## Features

- **Instant Document Upload & AI Summarization:**  
  Upload or capture any contract/notice. Google Document AI extracts and parses all contents, which are then passed to the PaLM model for complex legal term identification.
- **Smart Knowledge Routing:**  
  Legal terms and content are routed by a custom agent and MCP server to the appropriate database or knowledge graph for explanation and look-up.
- **Authoritative Legal Definitions:**  
  Definitions and relationships powered by the Ministry of Justice & Law dictionary, modeled as knowledge graphs in Cloud Spanner.
- **Indian Law Book Integration:**  
  Full text and indices of BNS, BNSS, BSA, Consumer Rights stored in AlloyDB, accessible through fast retrieval and vector search.
- **Lightning-fast Dictionary Explorer:**  
  Redis and Valkey provide instant caching for legal dictionaries and semantic embeddings (Gemma).
- **Real-Time Risk Alerts:**  
  (Coming Soon) NLP-powered agent instantly warns users of risky or unfair contract terms before signing.
- **Multilingual and Voice-Enabled:**  
  (Planned) Seamless support for all major Indian languages and voice chat via Google Translate/Voice APIs.
- **Uncompromising Security & Audit:**  
  Data protection by Firebase Auth, Google IAM, encryption via KMS, immutable blockchain audit with GCUL, and fully secure document storage.
- **Chatbot Interface:**  
  AI-powered chatbot presents contract summaries, term explanations, and rapid answers (built on Flutter + Python backend).

---


## Security & Compliance

- User data encrypted at rest and in transit (Cloud KMS)
- Immutable audit trail with GCUL blockchain logging
- Role-based access via Google IAM/Firebase Auth
- Official sources (Ministry of Justice & Law, Indian law books)


## Quick Start

_Coming soon: complete deployment scripts and simple one-click start using Terraform or Docker._

1. Clone this repo and setup environment variables (`.env` templates provided)
2. Deploy frontend (Flutter) and backend (Python) services
3. Configure Google Cloud resources (Storage, Spanner, AlloyDB, Redis, KMS, IAM)
4. Connect Firebase project for authentication and storage
5. Run the app and upload your first legal document!

---

## Roadmap

- [x] Secure authentication, upload & summary in chatbot
- [ ] Retrieval of legal book answers, real-time risk alerts (NLP agent)
- [ ] Voice-to-voice and multilingual chat
- [ ] Blockchain-based audit for every document and transaction
- [ ] User-facing dictionary and law explorer UI

---


## **Contributors**

<table>
  <tr>
    <td align="center">
      <img src="https://avatars.githubusercontent.com/SajeevSenthil?s=300" width="100" alt="Sajeev Senthil" /><br/>
      <a href="https://github.com/SajeevSenthil"><b>Sajeev Senthil</b></a>
    </td>
        <td align="center">
      <img src="https://avatars.githubusercontent.com/Charuvarthan?s=300" width="100" alt="Charuvarthan" /><br/>
      <a href="https://github.com/Charuvarthan-T"><b>Charuvarthan</b></a>
    </td>
    <td align="center">
      <img src="https://avatars.githubusercontent.com/suganth07?s=300" width="100" alt="Suganth" /><br/>
      <a href="https://github.com/suganth07"><b>Suganth</b></a>
    </td>
    <td align="center">
      <img src="https://avatars.githubusercontent.com/abiruth29?s=300" width="100" alt="Abiruth" /><br/>
      <a href="https://github.com/abiruth29"><b>Abiruth</b></a>
    </td>
    <td align="center">
      <img src="https://avatars.githubusercontent.com/SivaPrasanthSivaraj?s=300" width="100" alt="Siva Prasanth Sivaraj" /><br/>
      <a href="https://github.com/SivaPrasanthSivaraj"><b>Siva Prasanth Sivaraj</b></a>
    </td>
  </tr>
</table>



## License

LegalLens is released under the MIT License.

---

*LegalLens — Bringing legal clarity, security, and confidence to everyone.*
