import React from 'react';
import PathCard from './PathCard';

function Results({ data, steamId }) {
    const { recommendations } = data;

    return (
        <section className="animate-in fade-in zoom-in duration-1000 pb-20">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-8">
                <PathCard
                    archetype="Modern Hit"
                    title={recommendations.modern.name}
                    type="modern"
                    summary={recommendations.modern.summary}
                    coverUrl={recommendations.modern.cover_url}
                    reasoning={recommendations.modern.reasoning}
                />
                <PathCard
                    archetype="Hidden Gem"
                    title={recommendations.gem.name}
                    type="gem"
                    summary={recommendations.gem.summary}
                    coverUrl={recommendations.gem.cover_url}
                    reasoning={recommendations.gem.reasoning}
                />
                <PathCard
                    archetype="Indie Spirit"
                    title={recommendations.indie.name}
                    type="indie"
                    summary={recommendations.indie.summary}
                    coverUrl={recommendations.indie.cover_url}
                    reasoning={recommendations.indie.reasoning}
                />
                <PathCard
                    archetype="Old Masterpiece"
                    title={recommendations.classic.name}
                    type="classic"
                    summary={recommendations.classic.summary}
                    coverUrl={recommendations.classic.cover_url}
                    reasoning={recommendations.classic.reasoning}
                />
            </div>
        </section>
    );
}

export default Results;
