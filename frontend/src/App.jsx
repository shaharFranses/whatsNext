import React, { useState, useEffect } from 'react';
import Landing from './components/Landing';
import Results from './components/Results';
import Concierge from './components/Concierge';
import Auth from './components/Auth';
import { supabase } from './lib/supabase';

function App() {
    const [session, setSession] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [data, setData] = useState(null);
    const [steamId, setSteamId] = useState('');
    const [isConciergeOpen, setIsConciergeOpen] = useState(false);

    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
        });

        const {
            data: { subscription },
        } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
        });

        return () => subscription.unsubscribe();
    }, []);

    const handleAnalyze = async (id = null) => {
        if (id) setSteamId(id);
        setAnalyzing(true);
        try {
            const token = session?.access_token;
            // If No ID is passed, we call the endpoint without it (backend will use linked ID)
            const url = id 
                ? `http://127.0.0.1:8000/api/analyze/${id}` 
                : `http://127.0.0.1:8000/api/analyze/`;
            
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Analysis failed');
            }
            
            const result = await response.json();
            setData(result);
        } catch (err) {
            console.error(err);
            alert(`Error: ${err.message}`);
        } finally {
            setAnalyzing(false);
        }
    };

    const handleSync = async (id) => {
        setAnalyzing(true);
        try {
            const token = session?.access_token;
            const response = await fetch('http://127.0.0.1:8000/api/steam/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ steam_id: id })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Sync failed');
            }
            
            // After successful sync, run analysis using the newly linked account
            await handleAnalyze();
        } catch (err) {
            console.error(err);
            alert(`Sync Error: ${err.message}`);
        } finally {
            setAnalyzing(false);
        }
    };

    const handleReset = () => {
        setData(null);
        setSteamId('');
    };

    const handleLogout = async () => {
        await supabase.auth.signOut();
        handleReset();
    };

    if (!session) {
        return (
            <div className="min-h-screen relative overflow-hidden bg-[#0a0a0c] flex items-center justify-center">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/20 blur-[120px] rounded-full" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/20 blur-[120px] rounded-full" />
                <Auth />
            </div>
        );
    }

    return (
        <div className="min-h-screen relative overflow-hidden bg-[#0a0a0c]">
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/20 blur-[120px] rounded-full" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/20 blur-[120px] rounded-full" />

            <div className="absolute top-8 right-8 z-50 flex items-center gap-4">
                <span className="text-xs text-gray-500 font-medium">{session.user.email}</span>
                <button
                    onClick={handleLogout}
                    className="px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5 transition-colors text-xs font-bold uppercase tracking-widest text-gray-400"
                >
                    Logout
                </button>
            </div>

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
                    <Landing 
                        onAnalyze={handleAnalyze} 
                        onSync={handleSync}
                        analyzing={analyzing} 
                        session={session}
                    />
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
