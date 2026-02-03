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

        outputPanel.innerHTML = '<span class="text-muted">Running...</span>'; // Use innerHTML to reset style

        try {
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            });

            const result = await response.json();

            if (result.error) {
                outputPanel.textContent = `Error:\n${result.stderr}`;
                outputPanel.style.color = '#ff6b6b'; // Custom danger color
            } else {
                outputPanel.textContent = result.stdout || '[No Output]';
                outputPanel.style.color = 'var(--text-color)';
            }
        } catch (error) {
            outputPanel.textContent = `Execution Error: ${error.message}`;
            outputPanel.style.color = '#ff6b6b';
        }
    });

    // Configure Marked
    marked.setOptions({
        highlight: function (code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'python';
            return hljs.highlight(code, { language }).value;
        },
        langPrefix: 'hljs language-',
        breaks: true,
        gfm: true
    });

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
            // Use marked for full markdown support
            contentDiv.innerHTML = marked.parse(text);

            // Post-processing for code blocks (Add Buttons)
            contentDiv.querySelectorAll('pre').forEach((pre) => {
                const container = document.createElement('div');
                container.className = 'code-container position-relative';

                // Button Group
                const btnGroup = document.createElement('div');
                btnGroup.className = 'code-actions position-absolute top-0 end-0 p-2 d-flex gap-2';

                // Copy Button
                const copyBtn = document.createElement('button');
                copyBtn.className = 'btn btn-sm btn-dark opacity-75';
                copyBtn.innerHTML = '<i class="bi bi-clipboard"></i>';
                copyBtn.title = 'Copy code';
                copyBtn.onclick = () => {
                    const code = pre.querySelector('code').innerText;
                    navigator.clipboard.writeText(code);
                    copyBtn.innerHTML = '<i class="bi bi-check2"></i>';
                    setTimeout(() => copyBtn.innerHTML = '<i class="bi bi-clipboard"></i>', 2000);
                };

                // Edit & Run Button
                const editRunBtn = document.createElement('button');
                editRunBtn.className = 'btn btn-sm btn-dark opacity-75';
                editRunBtn.innerHTML = '<i class="bi bi-pencil-square"></i> Edit & Run';
                editRunBtn.title = 'Edit and run in editor';
                editRunBtn.onclick = () => {
                    const code = pre.querySelector('code').innerText;
                    editor.value = code;
                    sidebar.classList.remove('collapsed');
                    runBtn.click(); // Trigger run
                };

                btnGroup.appendChild(copyBtn);
                btnGroup.appendChild(editRunBtn);

                // Wrap pre
                pre.parentNode.insertBefore(container, pre);
                container.appendChild(btnGroup);
                container.appendChild(pre);

                // Highlight code
                const codeBlock = pre.querySelector('code');
                if (codeBlock) hljs.highlightElement(codeBlock);
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
