// src/components/GetPdfContentButton.jsx

import React, { useState } from 'react';
import axios from 'axios';

const GetPdfContentButton = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState('');

    const handleGetContent = async () => {
        setLoading(true);
        setError(null);
        setSuccessMessage('');

        try {
            // 发送请求到后端的 deepseekAPI 以获取 PDF 内容
            const response = await axios.patch('http://47.98.142.70:8000/request_key_info');

            // 这里不需要对响应进行任何处理，如果后端返回信息可以直接展示
            if (response.status === 200) {
                setSuccessMessage('请求成功，已通过Deekseek获取论文要点信息。');
            } else {
                setError('请求失败，请重试。');
            }
        } catch (error) {
            if (error.response && error.response.status === 404) {
                setSuccessMessage('所有论文已获取核心要点。');
            } else {
                console.error('请求失败:', error);
                setError('请求失败，请重试。');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <button onClick={handleGetContent} disabled={loading}>
                {loading ? '请求中...' : '获取 PDF 核心内容'}
            </button>
            {error && <div style={{ color: 'red' }}>{error}</div>}
            {successMessage && <div style={{ color: 'green' }}>{successMessage}</div>}
        </div>
    );
};

export default GetPdfContentButton;

