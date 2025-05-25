import logo from './logo.svg';
import './App.css';
import React from 'react';
import PaperList from './components/PaperList';
import 'bootstrap/dist/css/bootstrap.min.css';
import FetchPapersButton from './components/fetchPapersButton';  // 确保路径正确

const App = () => {
    return (
        <div className="App">
            <h1>Academic Paper Tracker</h1>
            <FetchPapersButton />
            <PaperList />
        </div>
    );
};

export default App;
