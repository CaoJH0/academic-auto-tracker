import React, { useState } from 'react';

const FetchPapersButton = () => {
    const [response, setResponse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleFetchPapers = async () => {
        setLoading(true);
        setError(null);

        try {
            const res = await fetch('http://47.98.142.70:8000/fetch_papers', {
                method: 'POST', // 设置 HTTP 方法为 POST
                headers: {
                    'Content-Type': 'application/json', // 根据需求设置适当的请求头
                },
                // body: JSON.stringify({}) // 如果有需要传递的数据, 可以在这里提供
            });

            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }

            const data = await res.json();
            setResponse(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <button onClick={handleFetchPapers} disabled={loading}>
                {loading ? 'Loading...' : 'Fetch Papers'}
            </button>
            {response && (
                <div>
                    <h3>Response:</h3>
                    <pre>{JSON.stringify(response, null, 2)}</pre>
                </div>
            )}
            {error && (
                <div>
                    <h3>Error:</h3>
                    <pre>{error}</pre>
                </div>
            )}
        </div>
    );
};

export default FetchPapersButton;
