import { useState } from "react";
import { searchMovies } from "../services/api";
import "../styles/navbar.css";

export default function Navbar({
  onSelect,
  onOpenReco,
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  async function handleChange(e) {
    const q = e.target.value;
    setQuery(q);

    if (q.length < 2) {
      setResults([]);
      return;
    }

    try {
      const data = await searchMovies(q);
      setResults(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Search failed", err);
      setResults([]);
    }
  }

  return (
    <nav className="navbar">
      {/* LOGO */}
      <h1 className="logo">CiniMatch</h1>

      {/* SEARCH */}
      <input
        placeholder="Search movies, actors, genres..."
        value={query}
        onChange={handleChange}
      />

      {/* 🎯 PROFESSIONAL PERSONAL RECO CTA */}
      <button
        className="reco-btn"
        onClick={onOpenReco}
        aria-label="Personal movie recommendations"
      >
        <span className="reco-icon">🎯</span>
        <span className="reco-text">AI Recommends</span>
      </button>

      {/* SEARCH DROPDOWN */}
      {results.length > 0 && (
        <div className="search-results">
          {results.map((m) => (
            <div
              key={m.id}
              onClick={() => {
                onSelect(m);
                setResults([]);
                setQuery("");
              }}
            >
              {m.title}
            </div>
          ))}
        </div>
      )}
    </nav>
  );
}
