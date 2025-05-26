import logo from './logo.svg';
import './App.css';
import React from 'react';
import PaperList from './components/PaperList';
import 'bootstrap/dist/css/bootstrap.min.css';
import FetchPapersButton from './components/fetchPapersButton';  // 确保路径正确
import DownloadButton from './components/DownloadButton';
import GetPdfContentButton from './components/GetPdfContentButton';

const App = () => {
    return (
        <div className="App">
            <h1>Academic Paper Tracker</h1>
            <FetchPapersButton />
	    <DownloadButton />
	    <GetPdfContentButton />
            <PaperList />
        </div>
    );
};

export default App;
