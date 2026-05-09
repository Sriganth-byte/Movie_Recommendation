import { useEffect, useState } from "react";
import { searchMovies } from "../services/api";
import "../styles/navbar.css";

export default function Navbar({ onSelect, onOpenReco }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const q = query.trim();

    if (q.length < 2) {
      setResults([]);
      setLoading(false);
      setError("");
      return;
    }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        setError("");
        const data = await searchMovies(q, 0, 8, {
          signal: controller.signal,
        });
        setResults(Array.isArray(data) ? data : []);
      } catch (err) {
        if (err.name !== "AbortError") {
          console.error("Search failed", err);
          setResults([]);
          setError("Search is unavailable");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }, 250);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [query]);

  function selectMovie(movie) {
    onSelect(movie);
    setResults([]);
    setQuery("");
    setError("");
  }

  const showDropdown = query.trim().length >= 2 && (loading || error || results.length > 0);

  return (
    <nav className="navbar">
      <h1 className="logo">CiniMatch</h1>

      <input
        aria-label="Search movies"
        placeholder="Search movies..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <button
        className="reco-btn"
        onClick={onOpenReco}
        aria-label="Personal movie recommendations"
      >
        <span className="reco-icon" aria-hidden="true">AI</span>
        <span className="reco-text">Recommends</span>
      </button>

      {showDropdown && (
        <div className="search-results">
          {loading && <div className="search-status">Searching...</div>}
          {error && <div className="search-status">{error}</div>}
          {!loading &&
            !error &&
            results.map((m) => (
              <button
                key={m.imdb_id || m.title}
                type="button"
                onClick={() => selectMovie(m)}
              >
                {m.title}
              </button>
            ))}
        </div>
      )}
    </nav>
  );
}
