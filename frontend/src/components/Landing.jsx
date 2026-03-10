import React, { useState } from 'react';

function Landing({ onAnalyze, analyzing }) {
    const [input, setInput] = useState('');

    const handleSubmit = () => {
        if (input.trim()) onAnalyze(input.trim());
    };

    return (
        <section className={`flex flex-col items-center justify-center space-y-12 transition-all duration-1000 ${analyzing ? 'blur-xl scale-95 opacity-50' : ''}`}>
            <header className="text-center space-y-4">
                <h1 className="text-5xl md:text-7xl font-bold tracking-tight glow-text bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    What Next?
                </h1>
                <p className="text-lg md:text-xl text-gray-400 font-light px-4">
                    Analyze your Steam DNA. Discover your next masterpiece.
                </p>
            </header>

            <div className="w-full max-w-xl">
                <div className="glass-panel p-2 rounded-2xl flex flex-col sm:flex-row items-center shadow-2xl gap-2 sm:gap-0">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Enter SteamID64..."
                            className="bg-transparent w-full sm:flex-1 px-4 py-3 sm:px-6 sm:py-4 outline-none text-center sm:text-left text-lg placeholder:text-gray-600"
                            disabled={analyzing}
                        />
                        <button
                            onClick={handleSubmit}
                            disabled={analyzing}
                            className="w-full sm:w-auto bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900 px-6 py-3 sm:px-8 sm:py-4 rounded-xl font-semibold transition-all shadow-lg active:scale-95"
                        >
                            {analyzing ? 'Analyzing DNA...' : 'Analyze'}
                        </button>
                </div>
                <p className="text-center mt-4 text-xs text-gray-600 tracking-widest uppercase">
                    Find your SteamID in profile URL or settings
                </p>
            </div>
        </section>
    );
}

export default Landing;
