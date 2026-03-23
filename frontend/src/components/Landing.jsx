import React, { useState } from 'react';

function Landing({ onAnalyze, onSync, analyzing, session }) {
    const [input, setInput] = useState('');

    const handleSubmit = () => {
        if (input.trim()) onAnalyze(input.trim());
    };

    const handleSync = () => {
        if (input.trim()) onSync(input.trim());
    };

    return (
        <section className="flex flex-col items-center justify-center space-y-12 relative">
            <header className="text-center space-y-4">
                <h1 className="text-5xl md:text-7xl font-bold tracking-tight glow-text bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    What Next?
                </h1>
                <p className="text-lg md:text-xl text-gray-400 font-light px-4">
                    Analyze your Steam DNA. Discover your next masterpiece.
                </p>
            </header>

            <div className="w-full max-w-xl space-y-4">
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
                            onClick={session ? handleSync : handleSubmit}
                            disabled={analyzing}
                            className="w-full sm:w-auto bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900 px-6 py-3 sm:px-8 sm:py-4 rounded-xl font-semibold transition-all shadow-lg active:scale-95"
                        >
                            {analyzing ? 'Analyzing DNA...' : (session ? 'Connect & Sync' : 'Analyze')}
                        </button>
                </div>
                
                {session && (
                    <div className="flex flex-col items-center">
                        <button
                            onClick={() => onAnalyze()}
                            disabled={analyzing}
                            className="text-xs text-gray-400 hover:text-white transition-colors underline underline-offset-4 decoration-gray-600"
                        >
                            Or analyze your already linked account
                        </button>
                    </div>
                )}

                <p className="text-center text-xs text-gray-600 tracking-widest uppercase">
                    Find your SteamID in profile URL or settings
                </p>
            </div>
            {analyzing && (
                <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#0a0a0c]/90 backdrop-blur-md animate-in fade-in duration-500">
                    <div className="relative w-32 h-32 flex items-center justify-center">
                        <div className="absolute inset-0 rounded-full border-4 border-blue-500/20" />
                        <div className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-[spin_1.5s_linear_infinite]" />
                        <div className="absolute inset-2 rounded-full border-4 border-purple-500/20" />
                        <div className="absolute inset-2 rounded-full border-4 border-purple-500 border-b-transparent animate-[spin_2s_linear_infinite_reverse]" />
                        <div className="w-16 h-16 bg-blue-500 rounded-full animate-pulse-ring shadow-[0_0_30px_rgba(59,130,246,0.5)] flex items-center justify-center">
                            <span className="text-2xl">🧬</span>
                        </div>
                    </div>
                    <h3 className="mt-8 text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent animate-pulse">
                        Sequencing Steam DNA...
                    </h3>
                    <p className="mt-2 text-sm text-gray-400 tracking-widest uppercase">
                        Finding your next masterpiece
                    </p>
                </div>
            )}
        </section>
    );
}

export default Landing;
