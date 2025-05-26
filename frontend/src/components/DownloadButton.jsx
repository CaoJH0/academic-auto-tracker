// src/components/DownloadButton.jsx

import React, { useState } from 'react';
import axios from 'axios';

const DownloadButton = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState('');

    const handleDownload = async () => {
        setLoading(true);
        setError(null);
        setSuccessMessage('');

        try {
            // 发送 PATCH 请求到后端
            const response = await axios.patch('http://47.98.142.70:8000/download_pdfs', {
                // 添加请求体，必要时包含任何参数（如文件 ID 数组）
                fileIds: [1, 2, 3] // 这里根据后端要求添加参数
            });

            // 成功请求处理
            if (response.status === 200) {
                setSuccessMessage('下载请求成功！所有文件已保存在后台。');
            } else {
                
            }
        } catch (error) {
            // 处理 404 错误
            if (0) {
                setError('');
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
            <button onClick={handleDownload} disabled={loading}>
                {loading ? '正在请求下载...' : '批量下载 PDF'}
            </button>
            {error && <div style={{ color: 'red' }}>{error}</div>}
            {successMessage && <div style={{ color: 'green' }}>{successMessage}</div>}
        </div>
    );
};

export default DownloadButton;

