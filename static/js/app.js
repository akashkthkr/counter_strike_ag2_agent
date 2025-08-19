// Counter-Strike AG2 Web UI JavaScript

class CounterStrikeUI {
    constructor() {
        this.websocket = null;
        this.reconnectInterval = null;
        this.isConnected = false;
        this.gameState = {};
        this.lastChatLengths = [0, 0, 0, 0]; // Track chat lengths for each panel
        this.soundEnabled = true; // Sound effects enabled by default
        this.audioContext = null;
        
        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadInitialState();
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus('connected');
                if (this.reconnectInterval) {
                    clearInterval(this.reconnectInterval);
                    this.reconnectInterval = null;
                }
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.updateUI(data);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus('disconnected');
                this.scheduleReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('disconnected');
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.updateConnectionStatus('disconnected');
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        if (this.reconnectInterval) return;
        
        this.updateConnectionStatus('connecting');
        this.reconnectInterval = setInterval(() => {
            console.log('Attempting to reconnect...');
            this.setupWebSocket();
        }, 3000);
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        statusElement.className = status;
        
        switch (status) {
            case 'connected':
                statusElement.textContent = '🟢 Connected';
                break;
            case 'connecting':
                statusElement.textContent = '🟡 Reconnecting...';
                break;
            case 'disconnected':
                statusElement.textContent = '🔴 Disconnected';
                break;
        }
    }

    async loadInitialState() {
        try {
            const response = await fetch('/api/state');
            const data = await response.json();
            this.updateUI(data);
        } catch (error) {
            console.error('Failed to load initial state:', error);
        }
    }

    updateUI(data) {
        if (!data) return;
        
        this.gameState = data.game_state || {};
        
        // Update session info
        if (data.session_id) {
            document.getElementById('session-info').textContent = 
                `Session: ${data.session_id.substring(0, 8)}...`;
        }
        
        // Update terrorist panels
        if (data.terrorist_panels) {
            data.terrorist_panels.forEach((panel, index) => {
                const hadNewMessages = panel.chat_log.length > this.lastChatLengths[index];
                this.updateChatLog(`chat-${index}`, panel.chat_log, hadNewMessages);
                this.updateTriesCounter(`tries-${index}`, panel.rag_tries);
                this.lastChatLengths[index] = panel.chat_log.length;
            });
        }
        
        // Update CT panel
        if (data.ct_panel) {
            const hadNewMessages = data.ct_panel.chat_log.length > this.lastChatLengths[3];
            this.updateChatLog('chat-ct', data.ct_panel.chat_log, hadNewMessages);
            this.lastChatLengths[3] = data.ct_panel.chat_log.length;
        }
        
        // Update game state
        this.updateGameState();
    }

    updateChatLog(elementId, messages, hasNewMessages = false) {
        const chatElement = document.getElementById(elementId);
        if (!chatElement || !messages) return;
        
        chatElement.innerHTML = '';
        
        messages.forEach((message, index) => {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message';
            
            // Classify message type for styling
            if (message.startsWith('You:')) {
                messageDiv.classList.add('user');
            } else if (message.includes('Error:') || message.includes('❌')) {
                messageDiv.classList.add('error');
            } else if (message.includes('RAG:') || message.includes('AG2:') || 
                      message.includes('SMART:') || message.includes('CRITIC:') ||
                      message.includes('QUANT:') || message.includes('SOM:')) {
                messageDiv.classList.add('ai');
            } else {
                messageDiv.classList.add('system');
            }
            
            messageDiv.textContent = message;
            chatElement.appendChild(messageDiv);
            
            // Add pulse effect only for the truly new message
            if (hasNewMessages && index === messages.length - 1) {
                messageDiv.classList.add('pulse');
                
                // Play sound effect based on message content
                this.playActionSound(message);
            }
        });
        
        // Scroll to bottom
        chatElement.scrollTop = chatElement.scrollHeight;
    }

    updateTriesCounter(elementId, tries) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = `${tries} tries left`;
            
            // Color coding based on tries left
            if (tries <= 1) {
                element.style.backgroundColor = 'rgba(231, 76, 60, 0.3)';
            } else if (tries <= 3) {
                element.style.backgroundColor = 'rgba(243, 156, 18, 0.3)';
            } else {
                element.style.backgroundColor = 'rgba(46, 204, 113, 0.3)';
            }
        }
    }

    updateGameState() {
        const gameState = this.gameState;
        
        // Update round info
        const roundElement = document.getElementById('round-info');
        if (roundElement && gameState.round && gameState.max_rounds) {
            roundElement.textContent = `${gameState.round}/${gameState.max_rounds}`;
        }
        
        // Update score info
        const scoreElement = document.getElementById('score-info');
        if (scoreElement && gameState.round_scores) {
            const tScore = gameState.round_scores.Terrorists || 0;
            const ctScore = gameState.round_scores['Counter-Terrorists'] || 0;
            scoreElement.textContent = `T:${tScore} CT:${ctScore}`;
        }
        
        // Update bomb info
        const bombElement = document.getElementById('bomb-info');
        if (bombElement) {
            if (gameState.bomb_planted) {
                const site = gameState.bomb_site || 'unknown';
                bombElement.textContent = `💣 Planted at ${site}`;
                bombElement.style.color = '#e74c3c';
            } else {
                bombElement.textContent = 'Not planted';
                bombElement.style.color = '#95a5a6';
            }
        }
        
        // Update health info
        const healthElement = document.getElementById('health-info');
        if (healthElement && gameState.player_health) {
            let healthHTML = '';
            for (const [team, players] of Object.entries(gameState.player_health)) {
                const teamShort = team === 'Terrorists' ? 'T' : 'CT';
                const color = team === 'Terrorists' ? '#e74c3c' : '#3498db';
                
                healthHTML += `<div style="color: ${color}; font-weight: bold;">${teamShort}:</div>`;
                for (const [player, hp] of Object.entries(players)) {
                    const status = hp > 0 ? `${hp} HP` : 'DEAD';
                    const statusColor = hp > 0 ? '#2ecc71' : '#e74c3c';
                    healthHTML += `<div style="margin-left: 10px;">
                        ${player}: <span style="color: ${statusColor}">${status}</span>
                    </div>`;
                }
            }
            healthElement.innerHTML = healthHTML;
        }
    }

    setupEventListeners() {
        // Enter key support for all input fields
        document.querySelectorAll('.command-input').forEach((input, index) => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    if (input.id === 'input-ct') {
                        this.sendCTCommand();
                    } else {
                        this.sendTerroristCommand(index);
                    }
                }
            });
        });
        
        // Auto-focus on first input
        const firstInput = document.getElementById('input-0');
        if (firstInput) {
            firstInput.focus();
        }
    }

    playActionSound(message) {
        // Check if sound is enabled and audio context is available
        if (!this.soundEnabled || !window.AudioContext) return;
        
        const messageText = message.toLowerCase();
        let soundType = null;
        
        // Determine sound type based on message content
        if (messageText.includes('hit') || messageText.includes('shot') || messageText.includes('damage')) {
            soundType = 'shoot';
        } else if (messageText.includes('bomb') && messageText.includes('planted')) {
            soundType = 'bomb_plant';
        } else if (messageText.includes('defus')) {
            soundType = 'defuse';
        } else if (messageText.includes('dead') || messageText.includes('killed')) {
            soundType = 'death';
        } else if (messageText.includes('round') && (messageText.includes('win') || messageText.includes('won'))) {
            soundType = 'round_end';
        } else if (messageText.includes('error') || messageText.includes('❌')) {
            soundType = 'error';
        } else if (messageText.includes('rag:') || messageText.includes('ag2:') || messageText.includes('smart:')) {
            soundType = 'ai_response';
        }
        
        if (soundType) {
            this.playBeepSound(soundType);
        }
    }

    playBeepSound(type) {
        try {
            // Create audio context if not exists
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            const ctx = this.audioContext;
            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);
            
            // Configure sound based on type
            let frequency, duration, volume;
            
            switch (type) {
                case 'shoot':
                    // Create a more realistic shooting sound with multiple frequencies
                    this.playShootingSound();
                    return; // Don't play the simple beep
                case 'bomb_plant':
                    // Create a dramatic bomb planting sound
                    this.playBombPlantSound();
                    return;
                case 'defuse':
                    frequency = 600;
                    duration = 0.3;
                    volume = 0.3;
                    break;
                case 'death':
                    frequency = 200;
                    duration = 0.8;
                    volume = 0.2;
                    break;
                case 'round_end':
                    frequency = 1000;
                    duration = 1.0;
                    volume = 0.4;
                    break;
                case 'error':
                    frequency = 300;
                    duration = 0.2;
                    volume = 0.2;
                    break;
                case 'ai_response':
                    frequency = 1200;
                    duration = 0.15;
                    volume = 0.2;
                    break;
                default:
                    frequency = 500;
                    duration = 0.1;
                    volume = 0.2;
            }
            
            oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0, ctx.currentTime);
            gainNode.gain.linearRampToValueAtTime(volume, ctx.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);
            
            oscillator.start(ctx.currentTime);
            oscillator.stop(ctx.currentTime + duration);
            
        } catch (error) {
            console.log('Sound playback failed:', error);
        }
    }

    playShootingSound() {
        try {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            const ctx = this.audioContext;
            const now = ctx.currentTime;
            
            // Create a realistic gun fire sound with multiple components
            // 1. Muzzle Flash (very high frequency snap)
            const muzzleFlash = ctx.createOscillator();
            const muzzleGain = ctx.createGain();
            muzzleFlash.connect(muzzleGain);
            muzzleGain.connect(ctx.destination);
            
            muzzleFlash.frequency.setValueAtTime(3000, now);
            muzzleFlash.frequency.exponentialRampToValueAtTime(1500, now + 0.005);
            muzzleFlash.type = 'sawtooth';
            
            muzzleGain.gain.setValueAtTime(0.5, now);
            muzzleGain.gain.exponentialRampToValueAtTime(0.01, now + 0.02);
            
            muzzleFlash.start(now);
            muzzleFlash.stop(now + 0.02);
            
            // 2. Gun Fire Crack (sharp high frequency)
            const crack = ctx.createOscillator();
            const crackGain = ctx.createGain();
            crack.connect(crackGain);
            crackGain.connect(ctx.destination);
            
            crack.frequency.setValueAtTime(2200, now + 0.003);
            crack.frequency.exponentialRampToValueAtTime(900, now + 0.015);
            crack.type = 'square';
            
            crackGain.gain.setValueAtTime(0.6, now + 0.003);
            crackGain.gain.exponentialRampToValueAtTime(0.01, now + 0.06);
            
            crack.start(now + 0.003);
            crack.stop(now + 0.06);
            
            // 3. Main Explosion/Boom (mid frequency)
            const boom = ctx.createOscillator();
            const boomGain = ctx.createGain();
            boom.connect(boomGain);
            boomGain.connect(ctx.destination);
            
            boom.frequency.setValueAtTime(450, now + 0.008);
            boom.frequency.exponentialRampToValueAtTime(180, now + 0.12);
            boom.type = 'square';
            
            boomGain.gain.setValueAtTime(0.4, now + 0.008);
            boomGain.gain.exponentialRampToValueAtTime(0.01, now + 0.18);
            
            boom.start(now + 0.008);
            boom.stop(now + 0.18);
            
            // 4. Barrel Resonance (mid-low frequency)
            const barrel = ctx.createOscillator();
            const barrelGain = ctx.createGain();
            barrel.connect(barrelGain);
            barrelGain.connect(ctx.destination);
            
            barrel.frequency.setValueAtTime(280, now + 0.015);
            barrel.frequency.exponentialRampToValueAtTime(120, now + 0.25);
            barrel.type = 'triangle';
            
            barrelGain.gain.setValueAtTime(0.3, now + 0.015);
            barrelGain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
            
            barrel.start(now + 0.015);
            barrel.stop(now + 0.35);
            
            // 5. Echo/Reverb (low frequency)
            const echo = ctx.createOscillator();
            const echoGain = ctx.createGain();
            echo.connect(echoGain);
            echoGain.connect(ctx.destination);
            
            echo.frequency.setValueAtTime(150, now + 0.03);
            echo.frequency.exponentialRampToValueAtTime(60, now + 0.4);
            echo.type = 'sine';
            
            echoGain.gain.setValueAtTime(0.2, now + 0.03);
            echoGain.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
            
            echo.start(now + 0.03);
            echo.stop(now + 0.5);
            
            // 6. Enhanced white noise (gunpowder burn/gas escape)
            const noiseBuffer = ctx.createBuffer(1, ctx.sampleRate * 0.15, ctx.sampleRate);
            const noiseData = noiseBuffer.getChannelData(0);
            for (let i = 0; i < noiseData.length; i++) {
                // Create more realistic noise pattern
                const decay = 1 - (i / noiseData.length);
                noiseData[i] = (Math.random() * 2 - 1) * 0.15 * decay;
            }
            
            const noiseSource = ctx.createBufferSource();
            const noiseGain = ctx.createGain();
            noiseSource.buffer = noiseBuffer;
            noiseSource.connect(noiseGain);
            noiseGain.connect(ctx.destination);
            
            noiseGain.gain.setValueAtTime(0.4, now);
            noiseGain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);
            
            noiseSource.start(now);
            
            // 7. Shell Casing Drop (subtle metallic clink)
            setTimeout(() => {
                this.playShellCasing();
            }, 200);
            
        } catch (error) {
            console.log('Gun fire sound playback failed:', error);
            // Fallback to simple beep
            this.playBeepSound('default');
        }
    }

    playShellCasing() {
        try {
            if (!this.audioContext) return;
            
            const ctx = this.audioContext;
            const now = ctx.currentTime;
            
            // Create a subtle shell casing drop sound
            const casing = ctx.createOscillator();
            const casingGain = ctx.createGain();
            casing.connect(casingGain);
            casingGain.connect(ctx.destination);
            
            casing.frequency.setValueAtTime(1200, now);
            casing.frequency.exponentialRampToValueAtTime(800, now + 0.05);
            casing.type = 'triangle';
            
            casingGain.gain.setValueAtTime(0.1, now);
            casingGain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
            
            casing.start(now);
            casing.stop(now + 0.1);
            
        } catch (error) {
            console.log('Shell casing sound failed:', error);
        }
    }

    playBombPlantSound() {
        try {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            const ctx = this.audioContext;
            const now = ctx.currentTime;
            
            // Create a dramatic bomb planting sound sequence
            // 1. Initial beep sequence (like a timer starting)
            for (let i = 0; i < 3; i++) {
                const beep = ctx.createOscillator();
                const beepGain = ctx.createGain();
                beep.connect(beepGain);
                beepGain.connect(ctx.destination);
                
                beep.frequency.setValueAtTime(800, now + i * 0.15);
                beep.type = 'square';
                
                beepGain.gain.setValueAtTime(0.3, now + i * 0.15);
                beepGain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.15 + 0.1);
                
                beep.start(now + i * 0.15);
                beep.stop(now + i * 0.15 + 0.1);
            }
            
            // 2. Activation sound (lower frequency sweep)
            const activation = ctx.createOscillator();
            const activationGain = ctx.createGain();
            activation.connect(activationGain);
            activationGain.connect(ctx.destination);
            
            activation.frequency.setValueAtTime(200, now + 0.5);
            activation.frequency.exponentialRampToValueAtTime(400, now + 0.8);
            activation.type = 'sawtooth';
            
            activationGain.gain.setValueAtTime(0.4, now + 0.5);
            activationGain.gain.exponentialRampToValueAtTime(0.01, now + 1.0);
            
            activation.start(now + 0.5);
            activation.stop(now + 1.0);
            
            // 3. Final confirmation beep
            const confirm = ctx.createOscillator();
            const confirmGain = ctx.createGain();
            confirm.connect(confirmGain);
            confirmGain.connect(ctx.destination);
            
            confirm.frequency.setValueAtTime(1000, now + 0.9);
            confirm.type = 'sine';
            
            confirmGain.gain.setValueAtTime(0.3, now + 0.9);
            confirmGain.gain.exponentialRampToValueAtTime(0.01, now + 1.2);
            
            confirm.start(now + 0.9);
            confirm.stop(now + 1.2);
            
        } catch (error) {
            console.log('Bomb plant sound playback failed:', error);
            this.playBeepSound('default');
        }
    }

    async sendTerroristCommand(panelId) {
        const inputElement = document.getElementById(`input-${panelId}`);
        const text = inputElement.value.trim();
        
        if (!text) return;
        
        // Immediate UI feedback - show command instantly
        const chatElement = document.getElementById(`chat-${panelId}`);
        const immediateDiv = document.createElement('div');
        immediateDiv.className = 'chat-message user';
        immediateDiv.textContent = `You: ${text}`;
        chatElement.appendChild(immediateDiv);
        chatElement.scrollTop = chatElement.scrollHeight;
        
        // Show processing indicator
        const processingDiv = document.createElement('div');
        processingDiv.className = 'chat-message system processing';
        processingDiv.textContent = '⏳ Processing...';
        processingDiv.id = `processing-${panelId}-${Date.now()}`;
        chatElement.appendChild(processingDiv);
        chatElement.scrollTop = chatElement.scrollHeight;
        
        inputElement.value = '';
        inputElement.disabled = true;
        
        try {
            const response = await fetch(`/api/terrorist/${panelId}/input`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            // Remove processing indicator
            const processingElements = chatElement.querySelectorAll('.processing');
            processingElements.forEach(el => el.remove());
            
            // UI will be updated via WebSocket
            
        } catch (error) {
            console.error('Failed to send command:', error);
            // Add error message to chat
            const chatElement = document.getElementById(`chat-${panelId}`);
            const errorDiv = document.createElement('div');
            errorDiv.className = 'chat-message error';
            errorDiv.textContent = `Error: Failed to send command - ${error.message}`;
            chatElement.appendChild(errorDiv);
            chatElement.scrollTop = chatElement.scrollHeight;
        } finally {
            inputElement.disabled = false;
            inputElement.focus();
        }
    }

    async sendCTCommand() {
        const inputElement = document.getElementById('input-ct');
        const text = inputElement.value.trim();
        
        if (!text) return;
        
        // Immediate UI feedback - show command instantly
        const chatElement = document.getElementById('chat-ct');
        const immediateDiv = document.createElement('div');
        immediateDiv.className = 'chat-message user';
        immediateDiv.textContent = `You: ${text}`;
        chatElement.appendChild(immediateDiv);
        chatElement.scrollTop = chatElement.scrollHeight;
        
        // Show processing indicator
        const processingDiv = document.createElement('div');
        processingDiv.className = 'chat-message system processing';
        processingDiv.textContent = '⏳ Processing...';
        processingDiv.id = `processing-ct-${Date.now()}`;
        chatElement.appendChild(processingDiv);
        chatElement.scrollTop = chatElement.scrollHeight;
        
        inputElement.value = '';
        inputElement.disabled = true;
        
        try {
            const response = await fetch('/api/ct/input', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            // Remove processing indicator
            const processingElements = chatElement.querySelectorAll('.processing');
            processingElements.forEach(el => el.remove());
            
            // UI will be updated via WebSocket
            
        } catch (error) {
            console.error('Failed to send command:', error);
            // Add error message to chat
            const chatElement = document.getElementById('chat-ct');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'chat-message error';
            errorDiv.textContent = `Error: Failed to send command - ${error.message}`;
            chatElement.appendChild(errorDiv);
            chatElement.scrollTop = chatElement.scrollHeight;
        } finally {
            inputElement.disabled = false;
            inputElement.focus();
        }
    }
}

// Global functions for button onclick handlers
function sendTerroristCommand(panelId) {
    if (window.csui) {
        window.csui.sendTerroristCommand(panelId);
    }
}

function sendCTCommand() {
    if (window.csui) {
        window.csui.sendCTCommand();
    }
}

function toggleSound() {
    if (window.csui) {
        window.csui.soundEnabled = !window.csui.soundEnabled;
        const button = document.getElementById('sound-toggle');
        if (window.csui.soundEnabled) {
            button.textContent = '🔊 Sound ON';
            button.classList.remove('muted');
        } else {
            button.textContent = '🔇 Sound OFF';
            button.classList.add('muted');
        }
        
        // Play a test sound when enabling
        if (window.csui.soundEnabled) {
            window.csui.playBeepSound('ai_response');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.csui = new CounterStrikeUI();
});

// Handle page visibility changes to manage WebSocket connections
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, could pause updates
        console.log('Page hidden');
    } else {
        // Page is visible, ensure connection is active
        console.log('Page visible');
        if (window.csui && !window.csui.isConnected) {
            window.csui.setupWebSocket();
        }
    }
});
