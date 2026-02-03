document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const editor = document.getElementById('code-editor');
    const runBtn = document.getElementById('run-btn');
    const outputPanel = document.getElementById('output-content');
    const themeToggle = document.getElementById('theme-toggle');

    // Theme Toggle
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        themeToggle.textContent = newTheme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode';
    });

    // Send Message
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        appendMessage('user', message);
        messageInput.value = '';
        messageInput.disabled = true;
        sendBtn.disabled = true;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                appendMessage('ai', data.response);
                extractCodeToEditor(data.response);
            } else {
                appendMessage('ai', `Error: ${data.detail || 'Failed to get response'}`);
            }
        } catch (error) {
            appendMessage('ai', `Network Error: ${error.message}`);
        } finally {
            messageInput.disabled = false;
            sendBtn.disabled = false;
            messageInput.focus();
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Run Code
    runBtn.addEventListener('click', async () => {
        const code = editor.value;
        if (!code.trim()) return;

        outputPanel.textContent = 'Running...';
        
        try {
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            });
            
            const result = await response.json();
            
            if (result.error) {
                outputPanel.textContent = `Error:\n${result.stderr}`;
                outputPanel.style.color = 'var(--bs-danger)';
            } else {
                outputPanel.textContent = result.stdout || '[No Output]';
                outputPanel.style.color = 'var(--text-color)';
            }
        } catch (error) {
            outputPanel.textContent = `Execution Error: ${error.message}`;
        }
    });

    // Helper: Append Message
    function appendMessage(role, text) {
        const div = document.createElement('div');
        div.className = `message ${role}-message`;
        
        // Simple markdown parsing for code blocks
        // This is a naive implementation; for production use a library like 'marked'
        if (role === 'ai') {
            const parts = text.split(/```/);
            parts.forEach((part, index) => {
                if (index % 2 === 1) {
                    // Code block
                    const codeDiv = document.createElement('div');
                    codeDiv.className = 'code-block';
                    // Strip language identifier (first line)
                    const lines = part.split('\n');
                    const codeContent = lines.slice(1).join('\n'); // remove first line (e.g. 'python')
                    codeDiv.textContent = codeContent.trim();
                    div.appendChild(codeDiv);
                } else {
                    // Normal text
                    const p = document.createElement('p');
                    p.innerHTML = part.replace(/\n/g, '<br>').trim();
                    if(p.textContent) div.appendChild(p);
                }
            });
        } else {
            div.textContent = text;
        }

        chatContainer.appendChild(div);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Helper: Puts code into editor automatically if found
    function extractCodeToEditor(text) {
        const match = text.match(/```python\s([\s\S]*?)```/);
        if (match && match[1]) {
            editor.value = match[1].trim();
        }
    }
});
