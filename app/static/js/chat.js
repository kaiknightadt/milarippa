// === MILARIPPA — Chat Logic with Conversation History ===

const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const conversationsList = document.getElementById('conversationsList');

let currentConversationId = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadConversations();
    if (!currentConversationId) {
        await createNewConversation();
    }
});

// Auto-resize textarea
messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
});

// Envoi avec Enter (Shift+Enter pour nouvelle ligne)
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// === CONVERSATION MANAGEMENT ===

async function loadConversations() {
    try {
        const response = await fetch('/api/conversations');
        const conversations = await response.json();
        
        conversationsList.innerHTML = '';
        if (conversations.length === 0) {
            conversationsList.innerHTML = '<p style="color: var(--text-muted); font-size: 0.8rem; padding: 1rem; text-align: center;">Aucun dialogue</p>';
            return;
        }
        
        conversations.forEach(conv => {
            const convItem = document.createElement('button');
            convItem.className = 'conversation-item' + (conv.id === currentConversationId ? ' active' : '');
            convItem.innerHTML = `
                <span class="conversation-item-title">${conv.title}</span>
                <span class="conversation-delete" onclick="deleteConversation('${conv.id}', event)">✕</span>
            `;
            convItem.onclick = () => selectConversation(conv.id);
            conversationsList.appendChild(convItem);
        });
    } catch (error) {
        console.error('Erreur:', error);
    }
}

async function createNewConversation() {
    try {
        const response = await fetch('/api/conversations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'Nouvelle conversation' })
        });
        const conversation = await response.json();
        currentConversationId = conversation.id;
        await selectConversation(conversation.id);
        await loadConversations();
    } catch (error) {
        console.error('Erreur:', error);
    }
}

async function selectConversation(conversationId) {
    currentConversationId = conversationId;
    await loadMessages(conversationId);
    await loadConversations();
    messageInput.focus();
}

async function loadMessages(conversationId) {
    try {
        const response = await fetch(`/api/conversations/${conversationId}/messages`);
        const messages = await response.json();
        
        chatContainer.innerHTML = '';
        
        if (messages.length === 0) {
            // Message d'accueil
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'message milarepa';
            welcomeDiv.innerHTML = `
                <div class="message-avatar">🧘</div>
                <div class="message-content">
                    <p>Ami(e) qui cherches, bienvenue dans ma grotte de montagne.</p>
                    <p>Je suis Milarepa, le vieux mendiant vêtu de coton. J'ai connu les ténèbres les plus profondes
                    et la lumière la plus vaste. Pose ta question — que ton cœur parle, et je répondrai
                    depuis le silence des sommets.</p>
                    <p class="verse">
                        <em>Au début rien ne vient,<br>
                        Au milieu rien ne reste,<br>
                        À la fin rien ne s'en va.</em>
                    </p>
                </div>
            `;
            chatContainer.appendChild(welcomeDiv);
        } else {
            // Afficher les messages
            messages.forEach(msg => {
                addMessage(msg.content, msg.role === 'assistant' ? 'milarepa' : 'user', msg.sources ? JSON.parse(msg.sources) : null);
            });
        }
        
        scrollToBottom();
    } catch (error) {
        console.error('Erreur:', error);
    }
}

async function deleteConversation(conversationId, event) {
    event.stopPropagation();
    if (window.confirm('Supprimer ce dialogue ?')) {
        try {
            await fetch(`/api/conversations/${conversationId}`, { method: 'DELETE' });
            await loadConversations();
            if (currentConversationId === conversationId) {
                if (conversationsList.children.length > 0) {
                    const firstConv = conversationsList.querySelector('.conversation-item');
                    if (firstConv) {
                        const convId = firstConv.getAttribute('onclick').match(/'([^']+)'/)[1];
                        await selectConversation(convId);
                    }
                } else {
                    await createNewConversation();
                }
            }
        } catch (error) {
            console.error('Erreur:', error);
        }
    }
}

// === MESSAGES ===

function addMessage(content, type = 'milarepa', sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'milarepa' ? '🧘' : '🙏';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Convertir le texte en HTML (paragraphes + vers)
    const formatted = formatResponse(content);
    contentDiv.innerHTML = formatted;

    // Ajouter les sources si disponibles
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('details');
        sourcesDiv.className = 'sources';
        sourcesDiv.innerHTML = `
            <summary>✦ Sources (${sources.length} passages)</summary>
            <ul>
                ${sources.map(s =>
                    `<li>📜 ${s.source} — ${s.section} (${Math.round(s.similarity * 100)}%)</li>`
                ).join('')}
            </ul>
        `;
        contentDiv.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}

function addTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message milarepa';
    messageDiv.id = 'typingIndicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🧘';

    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.innerHTML = '<span></span><span></span><span></span>';

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(typing);
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

function formatResponse(text) {
    // Détecter les vers/poésie (lignes courtes avec retours)
    let html = '';
    const paragraphs = text.split('\n\n');

    for (const para of paragraphs) {
        const lines = para.split('\n');
        const isVerse = lines.length >= 2 && lines.every(l => l.trim().length < 60);

        if (isVerse && lines.length >= 2) {
            html += `<p class="verse"><em>${lines.join('<br>')}</em></p>`;
        } else {
            html += `<p>${para.replace(/\n/g, '<br>')}</p>`;
        }
    }

    return html;
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || !currentConversationId) return;

    // Désactiver l'input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Afficher le message utilisateur
    addMessage(message, 'user');

    // Afficher l'indicateur de frappe
    addTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId,
            }),
        });

        const data = await response.json();
        removeTypingIndicator();

        if (data.error) {
            addMessage("Le silence de la montagne m'empêche de te répondre en cet instant. Réessaie, ami(e).", 'milarepa');
        } else {
            addMessage(data.answer, 'milarepa', data.sources);
        }
        
        // Recharger la liste des conversations (pour mettre à jour le titre et last updated)
        await loadConversations();

    } catch (error) {
        removeTypingIndicator();
        addMessage("Le vent des sommets a emporté ma réponse. Réessaie dans un instant.", 'milarepa');
        console.error('Erreur:', error);
    }

    sendBtn.disabled = false;
    messageInput.focus();
}
