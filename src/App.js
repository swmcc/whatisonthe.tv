import './App.css';
import Search from './Search';
import Footer from './Footer';

function App() {
  return (
    <div className="App">
      <div className="flex justify-center items-center">
        <img src="images/icon.png" alt="whatisonthe.tv" className="object-contain" />
      </div>
      <Search />
      <Footer />
    </div>
  );
}

export default App;
