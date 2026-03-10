document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const analyzeBtn = document.getElementById('analyzeBtn');
    const steamIdInput = document.getElementById('steamIdInput');
    const landingSection = document.getElementById('landing');
    const resultsSection = document.getElementById('results');
    const toggleConcierge = document.getElementById('toggleConcierge');
    const conciergeSidebar = document.getElementById('concierge');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');

    // State
    let isAnalyzing = false;

    // Toggle Concierge Sidebar
    toggleConcierge.addEventListener('click', () => {
        conciergeSidebar.classList.toggle('open');
    });

    // Handle Analysis
    analyzeBtn.addEventListener('click', async () => {
        const steamId = steamIdInput.value.trim();
        if (!steamId) {
            alert('Please enter a valid SteamID');
            return;
        }

        if (isAnalyzing) return;
        startAnalysis();

        try {
            const response = await fetch(`http://127.0.0.1:8001/api/analyze/${steamId}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to analyze SteamID.');
            }
            const data = await response.json();

            // Map real Phase 2 recommendations to UI
            const recs = data.recommendations;
            showResults({
                modern: recs.modern?.name || "No modern hits found",
                gem: recs.gem?.name || "No hidden gems found",
                indie: recs.indie?.name || "No indie spirits found",
                classic: recs.classic?.name || "No old masterpieces found"
            });

            // Update concierge with DNA info
            setTimeout(() => {
                const dnaTags = data.dna.slice(0, 3).join(', ');
                addChatMessage('Concierge', `Analysis complete! Your gaming DNA is dominated by **${dnaTags}**. Based on this, I've curated four distinct paths for you.`);
            }, 1000);

        } catch (error) {
            alert(error.message);
            stopAnalysis();
        }
    });

    function stopAnalysis() {
        isAnalyzing = false;
        analyzeBtn.textContent = 'Analyze';
        analyzeBtn.disabled = false;
        steamIdInput.disabled = false;
        landingSection.style.filter = 'none';
    }

    function startAnalysis() {
        isAnalyzing = true;
        analyzeBtn.textContent = 'Analyzing...';
        analyzeBtn.disabled = true;
        steamIdInput.disabled = true;

        // Visual feedback
        landingSection.style.filter = 'blur(5px)';
        landingSection.style.transition = 'filter 1s ease';
    }

    function showResults(data) {
        isAnalyzing = false;
        landingSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');

        // Populate cards
        document.querySelector('#card-modern .game-title').textContent = data.modern;
        document.querySelector('#card-gem .game-title').textContent = data.gem;
        document.querySelector('#card-indie .game-title').textContent = data.indie;
        document.querySelector('#card-classic .game-title').textContent = data.classic;

        // Auto-open concierge with a welcome message
        setTimeout(() => {
            conciergeSidebar.classList.add('open');
            addChatMessage('System', `I've analyzed your profile. Based on your love for deep narratives, I highly recommend starting with ${data.gem}. It fits your "Discovery" pattern.`);
        }, 1000);
    }

    // Chat functionality
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && chatInput.value.trim()) {
            const userMsg = chatInput.value.trim();
            addChatMessage('You', userMsg);
            chatInput.value = '';

            // Simulated AI response
            setTimeout(() => {
                addChatMessage('Concierge', "That's a great question! Based on the achievements in your library, that game might be a bit too grindy for your current mood. How about something shorter?");
            }, 1000);
        }
    });

    function addChatMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender.toLowerCase()}`;
        msgDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
