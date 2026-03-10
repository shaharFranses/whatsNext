import React, { useState } from 'react';
import Landing from './components/Landing';
import Results from './components/Results';
import Concierge from './components/Concierge';

function App() {
    const [analyzing, setAnalyzing] = useState(false);
    const [data, setData] = useState(null);
    const [steamId, setSteamId] = useState('');
    const [isConciergeOpen, setIsConciergeOpen] = useState(false);

    const handleAnalyze = async (id) => {
        setSteamId(id);
        setAnalyzing(true);
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/analyze/${id}`);
            if (!response.ok) throw new Error('Analysis failed');
            const result = await response.json();
            setData(result);
        } catch (err) {
            console.error(err);
            alert('Error analyzing Steam profile');
        } finally {
            setAnalyzing(false);
        }
    };

    const handleReset = () => {
        setData(null);
        setSteamId('');
    };

    return (
        <div className="min-h-screen relative overflow-hidden bg-[#0a0a0c]">
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/20 blur-[120px] rounded-full" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/20 blur-[120px] rounded-full" />

            <main className={`container mx-auto px-4 py-20 relative z-10 transition-all duration-500 ease-in-out ${isConciergeOpen ? 'md:pr-[400px]' : ''}`}>
                {data && (
                    <div className="flex justify-between items-center mb-12 animate-in slide-in-from-top duration-700 max-w-7xl mx-auto">
                        <h1 className="text-4xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                            What Next?
                        </h1>
                        <button
                            onClick={handleReset}
                            className="px-6 py-2 rounded-full border border-white/10 hover:bg-white/5 transition-colors text-sm font-bold uppercase tracking-widest text-gray-400"
                        >
                            Analyze Another Profile
                        </button>
                    </div>
                )}

                {!data ? (
                    <Landing onAnalyze={handleAnalyze} analyzing={analyzing} />
                ) : (
                    <div className="max-w-7xl mx-auto">
                        <Results data={data} steamId={steamId} />
                    </div>
                )}
            </main>

            <Concierge
                initialData={data}
                isOpen={isConciergeOpen}
                setIsOpen={setIsConciergeOpen}
            />
        </div>
    );
}

export default App;
