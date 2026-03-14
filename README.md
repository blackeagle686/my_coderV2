# 🤖 AI Coder Assistant

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Qwen2.5-Coder](https://img.shields.io/badge/Model-Qwen2.5--Coder--3B-7e57c2.svg)](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful, web-based AI coding assistant powered by **Qwen2.5-Coder-3B-Instruct**. This tool provides an interactive chat interface for code generation, explanation, and execution within a secure, AST-validated sandbox.

---

## 🚀 About the Project

AI Coder Assistant is designed to bridge the gap between AI-driven code generation and immediate validation. It allows developers to converse with a state-of-the-art LLM optimized for coding, get instant code solutions, and run them safely in a restricted environment.

### Key Features
- **Intelligent Coding Partner**: Powered by Qwen 2.5 Coder, specialized for code generation and debugging.
- **Contextual Memory**: Automatically summarizes long conversations to maintain coherent context without hitting token limits.
- **Secure Sandbox**: Executes Python code using a custom AST-based validator that blocks dangerous operations (file system access, network calls, etc.).
- **Modern Web Interface**: A sleek, responsive UI for seamless interaction.

---

## 🛠 Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - High-performance Python web framework.
- **Inference**: [Hugging Face Transformers](https://huggingface.co/docs/transformers/index) & [PyTorch](https://pytorch.org/).
- **Model**: `Qwen/Qwen2.5-Coder-3B-Instruct` - A state-of-the-art open coding model.
- **Security**: Python AST (Abstract Syntax Trees) for code validation.

### Frontend
- **Structure**: Semantic HTML5.
- **Styling**: Modern CSS3 with a focus on UX and responsiveness.
- **Logic**: Vanilla JavaScript for real-time API interaction.

---

## 📐 Workflow and Architecture

The system follows a modular agent architecture with secure execution and AI reasoning services.

```mermaid
graph TD

User((User)) <---> UI[Frontend UI]

UI <---> API[FastAPI Backend]

subgraph Backend
API --> AI[AI Service]
API --> Sandbox[Code Sandbox]
end

subgraph AI_System
AI --> LLM[Qwen2.5-Coder-3B]
AI --> Memory[Context Summarizer]
end

subgraph Secure_Execution
Sandbox --> Validator{AST Security Check}

Validator -->|Safe| Executor[Python Executor]

Validator -->|Unsafe| Error[Security Exception]
end

Executor --> API

AI --> API

API --> UI
### Process Flow
1. **Chat**: User sends a prompt -> FastAPI forwards to Qwen AI Service -> Model generates code/response -> History is updated and summarized if needed.
2. **Execution**: User clicks 'Run' -> FastAPI forwards code to Sandbox -> AST Validator checks for blacklisted calls -> If safe, code executes in a separate process -> Results returned to UI.

---

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/my_coder.git
   cd my_coder
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python -m app.main
   ```
   Access the UI at `http://localhost:8000`.

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.
y_coderV2
