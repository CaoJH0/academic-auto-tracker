import logo from './logo.svg';
import './App.css';
import React from 'react';
import PaperList from './components/PaperList';
import 'bootstrap/dist/css/bootstrap.min.css';


// function App() {
//   return (
//     <div className="App">
//       <header className="App-header">
//         <img src={logo} className="App-logo" alt="logo" />
//         <p>
//           Edit <code>src/App.js</code> and save to reload.
//         </p>
//         <a
//           className="App-link"
//           href="https://reactjs.org"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           Learn React
//         </a>
//       </header>
//     </div>
//   );
// }

const App = () => {
    return (
        <div className="App">
            <h1>Academic Paper Tracker</h1>
            <PaperList />
        </div>
    );
};

export default App;
