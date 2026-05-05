// Global variables
let chatbotExpanded = false;
let chatSessionId = generateSessionId();

// Generate session ID
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9);
}

// Toggle chatbot
function toggleChat() {
    const chatBody = document.getElementById('chatBody');
    const chatToggle = document.getElementById('chatToggle');
    
    chatbotExpanded = !chatbotExpanded;
    
    if (chatbotExpanded) {
        chatBody.style.display = 'flex';
        chatToggle.style.transform = 'rotate(180deg)';
    } else {
        chatBody.style.display = 'none';
        chatToggle.style.transform = 'rotate(0deg)';
    }
}

// Send message
function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (message === '') return;
    
    // Add user message to chat
    addUserMessage(message);
    
    // Send to server (if socket exists)
    if (typeof socket !== 'undefined' && socket) {
        socket.emit('chat_message', {
            message: message,
            session_id: chatSessionId
        });
    }
    
    // Clear input
    input.value = '';
}

// Add user message
function addUserMessage(message) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'user-message';
    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(message)}</div>
    `;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add bot message
function addBotMessage(message) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'bot-message';
    messageDiv.innerHTML = `
        <i class="fas fa-robot"></i>
        <div class="message-content">${escapeHtml(message)}</div>
    `;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// Show notification
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;
    
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Handle Enter key in chat
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Initialize socket for chatbot (only if not on attendance page)
    if (typeof socket === 'undefined' && typeof io !== 'undefined') {
        window.socket = io();
        
        socket.on('connect', function() {
            console.log('Socket connected for chatbot');
        });
        
        socket.on('chat_response', function(data) {
            addBotMessage(data.message);
        });
    }
});