import axios from 'axios';

const API_URL = 'http://localhost:8000'; // FastAPI 后端地址

export const fetchPapers = async () => {
    try {
        const response = await axios.get(`${API_URL}/papers`);
        console.log('Fetched papers:', response.data); // 添加调试信息
        return response.data;
    } catch (error) {
        console.error('Error fetching papers:', error);
        throw error;  // 抛出错误，以便在组件中处理
    }
};

