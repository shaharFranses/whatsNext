import React, { useState, useEffect } from 'react';

function Concierge({ initialData, isOpen, setIsOpen }) {
    const [messages, setMessages] = useState([
        { sender: 'System', text: "Hello! I'm your AI gaming guide. Analyze your library to get started." }
    ]);
    const [input, setInput] = useState('');

    useEffect(() => {
        if (initialData) {
            setTimeout(() => {
                setIsOpen(true);
                const dnaTags = initialData.dna.slice(0, 3).join(', ');
                setMessages(prev => [...prev, {
                    sender: 'Concierge',
                    text: `Analysis complete! Your gaming DNA is dominated by **${dnaTags}**. Based on this, I've curated four distinct paths for you.`
                }]);
            }, 1000);
        }
    }, [initialData]);

    const handleSend = () => {
        if (!input.trim()) return;
        setMessages(prev => [...prev, { sender: 'You', text: input }]);
        setInput('');

        // Simulated chat response
        setTimeout(() => {
            setMessages(prev => [...prev, {
                sender: 'Concierge',
                text: "That's a great question! Based on your playtime trends, you seem to appreciate deep systems but limited 'grind'. Does that sound right?"
            }]);
        }, 1000);
    };

    return (
        <aside 
            className="fixed top-0 h-full w-[100vw] sm:w-96 glass-panel z-50 transition-all duration-500 ease-in-out"
            style={{ right: isOpen ? '0' : '-100vw' }}
        >
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full bg-blue-600 p-3 sm:p-4 rounded-l-2xl shadow-xl hover:bg-blue-500 transition-colors z-50 group"
                >
                    <span className="text-xl sm:text-2xl block group-hover:scale-110 transition-transform">💬</span>
                </button>
            )}

            <div className="flex flex-col h-full bg-[#0a0a0c]/80 backdrop-blur-2xl border-l border-white/10">
                <div className="p-6 sm:p-8 border-b border-white/10 flex justify-between items-center">
                    <h3 className="text-lg sm:text-xl font-bold tracking-widest uppercase text-blue-400">Concierge</h3>
                    <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white p-2">
                        <span className="text-xl">✕</span>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-8 space-y-6 scrollbar-hide">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`space-y-1 ${msg.sender === 'You' ? 'text-right' : ''}`}>
                            <div className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">
                                {msg.sender}
                            </div>
                            <div className={`inline-block p-4 rounded-2xl text-sm leading-relaxed ${msg.sender === 'You' ? 'bg-blue-600 text-white rounded-tr-none' : 'glass-panel rounded-tl-none'}`}>
                                {msg.text}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="p-8">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Ask about your next play..."
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-6 py-4 text-sm outline-none focus:border-blue-500 transition-colors"
                    />
                </div>
            </div>
        </aside>
    );
}

export default Concierge;
