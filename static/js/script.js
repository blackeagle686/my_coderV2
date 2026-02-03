document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const editor = document.getElementById('code-editor');
    const runBtn = document.getElementById('run-btn');
    const outputPanel = document.getElementById('output-content');
    const themeToggle = document.getElementById('theme-toggle');
    const sidebar = document.getElementById('code-sidebar');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar');
    const aiLoading = document.getElementById('ai-loading');

    // Toggle Sidebar
    toggleSidebarBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // Theme Toggle
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);

        const icon = themeToggle.querySelector('i');
        if (newTheme === 'light') {
            icon.className = 'bi bi-moon';
        } else {
            icon.className = 'bi bi-sun';
        }
    });

    // Send Message
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        appendMessage('user', message);
        messageInput.value = '';
        messageInput.disabled = true;
        sendBtn.disabled = true;

        // Show Loading
        aiLoading.classList.remove('d-none');
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            // Hide Loading
            aiLoading.classList.add('d-none');

            if (response.ok) {
                appendMessage('ai', data.response);
                extractCodeToEditor(data.response);
                // Automatically open sidebar if code is generated
                if (data.response.includes('```')) {
                    sidebar.classList.remove('collapsed');
                }
            } else {
                appendMessage('ai', `Error: ${data.detail || 'Failed to get response'}`);
            }
        } catch (error) {
            aiLoading.classList.add('d-none');
            appendMessage('ai', `Network Error: ${error.message}`);
        } finally {
            messageInput.disabled = false;
            sendBtn.disabled = false;
            messageInput.focus();
        }
    }

    // ... [OMITTED SEND/RUN LOGIC] ...

    // Helper: Append Message
    function appendMessage(role, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}-message`;

        // Avatar
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        const icon = document.createElement('i');
        icon.className = role === 'ai' ? 'bi bi-robot' : 'bi bi-person-fill';
        avatarDiv.appendChild(icon);

        // Content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (role === 'ai') {
            const parts = text.split(/```/);
            parts.forEach((part, index) => {
                if (index % 2 === 1) {
                    // Code block
                    const pre = document.createElement('pre');
                    pre.className = 'code-block';
                    const code = document.createElement('code');

                    const lines = part.split('\n');
                    let language = 'python';
                    let codeContent = part;

                    if (lines[0].trim().length > 0 && !lines[0].includes('=')) {
                        language = lines[0].trim();
                        codeContent = lines.slice(1).join('\n');
                    }

                    code.className = `language-${language}`;
                    code.textContent = codeContent.trim();
                    pre.appendChild(code);
                    contentDiv.appendChild(pre);
                    hljs.highlightElement(code);
                } else {
                    const p = document.createElement('p');
                    p.innerHTML = part.replace(/\n/g, '<br>').trim();
                    if (p.textContent) contentDiv.appendChild(p);
                }
            });
        } else {
            const p = document.createElement('p');
            p.textContent = text;
            contentDiv.appendChild(p);
        }

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        chatContainer.appendChild(messageDiv);
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
