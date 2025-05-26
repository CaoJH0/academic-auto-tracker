import React, { useEffect, useState } from 'react';
import { fetchPapers } from '../api';
import PaperItem from './PaperItem';

const PaperList = () => {
    const [papers, setPapers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const getPapers = async () => {
            try {
                const data = await fetchPapers();
		const filteredPapers = data.filter(paper => !paper.key_info || !paper.key_info.error);
                setPapers(filteredPapers);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        getPapers();
    }, []);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div className="container">
            <div className="row">
                {papers.map((paper) => (
                    <PaperItem key={paper.doi} paper={paper} />
                ))}
            </div>
        </div>
    );
};

export default PaperList;
