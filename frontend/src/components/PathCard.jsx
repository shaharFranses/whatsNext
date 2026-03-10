import React, { useState } from 'react';

function PathCard({ archetype, title, type, summary, coverUrl, reasoning }) {
    const [isExpanded, setIsExpanded] = useState(false);
    const glowColors = {
        modern: 'from-blue-500/40 to-cyan-500/40',
        gem: 'from-emerald-500/40 to-teal-500/40',
        indie: 'from-amber-500/40 to-orange-500/40',
        classic: 'from-purple-500/40 to-pink-500/40',
    };

    const accentColors = {
        modern: 'text-blue-400',
        gem: 'text-emerald-400',
        indie: 'text-amber-400',
        classic: 'text-purple-400',
    };

    const borderColors = {
        modern: 'border-blue-500/30',
        gem: 'border-emerald-500/30',
        indie: 'border-amber-500/30',
        classic: 'border-purple-500/30',
    };

    return (
        <div className={`group relative glass-panel rounded-3xl h-full flex flex-col overflow-hidden transition-all duration-500 hover:scale-[1.02] hover:-translate-y-2 border-2 ${borderColors[type]}`}>
            {/* Game Art Background */}
            <div className="absolute inset-x-0 top-0 h-64 overflow-hidden">
                <img
                    src={coverUrl}
                    alt={title}
                    className="w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0c] via-transparent to-transparent" />
            </div>

            <div className={`absolute inset-0 bg-gradient-to-br ${glowColors[type]} opacity-10 group-hover:opacity-30 transition-opacity`} />

            <div className="relative z-10 p-6 sm:p-8 pt-64 flex-1 flex flex-col justify-start gap-4">
                <div className="space-y-2">
                    <div className="flex justify-between items-start">
                        <span className={`text-[10px] uppercase tracking-[0.3em] font-black ${accentColors[type]}`}>
                            {archetype}
                        </span>
                    </div>
                    <h2 className="text-2xl sm:text-3xl font-black leading-tight drop-shadow-lg">
                        {title}
                    </h2>
                </div>

                <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                    <span className="text-[9px] uppercase tracking-widest text-gray-500 font-bold">Why you'll love it</span>
                    <p className="text-xs text-gray-300 italic font-medium leading-relaxed">
                        "{reasoning}"
                    </p>
                </div>

                <div className="space-y-2">
                    <p className={`text-gray-400 text-sm font-light leading-relaxed transition-all duration-500 ${isExpanded ? '' : 'line-clamp-3'}`}>
                        {summary}
                    </p>
                    <button 
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="text-[10px] uppercase tracking-widest font-bold text-gray-500 hover:text-white transition-colors flex items-center gap-1 mt-2"
                    >
                        {isExpanded ? 'Show Less ▲' : 'Read Full Description ▼'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default PathCard;
