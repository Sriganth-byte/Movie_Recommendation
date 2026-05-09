import { useCallback, useEffect, useState } from "react";
import "../styles/hallOfFame.css";

const BACKDROP = "https://image.tmdb.org/t/p/original";
const POSTER = "https://image.tmdb.org/t/p/w500";

export default function HallOfFame({ movies = [], onSelect }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!movies.length) return;
    setIndex(0);
    const timer = setInterval(
      () => setIndex((i) => (i + 1) % movies.length),
      5000
    );
    return () => clearInterval(timer);
  }, [movies.length]);

  const m = movies[Math.min(index, movies.length - 1)];

  const handleSelect = useCallback(() => onSelect(m), [m, onSelect]);

  if (!movies.length || !m) return null;

  const bgImage = m.backdrop_path
    ? `${BACKDROP}${m.backdrop_path}`
    : m.poster_path
    ? `${POSTER}${m.poster_path}`
    : null;

  return (
    <section
      className="hall"
      style={{ backgroundImage: bgImage ? `url(${bgImage})` : "none" }}
    >
      <div className="hall-overlay" />

      <div className="overlay-content">
        {m.poster_path && (
          <img
            src={`${POSTER}${m.poster_path}`}
            alt={m.title}
            className="hall-poster"
          />
        )}

        <div className="hall-text">
          <h2>Top Picks</h2>
          <h1>{m.title}</h1>
          <p>{m.overview || "No description available."}</p>

          <button type="button" onClick={handleSelect}>View Details</button>
        </div>
      </div>
    </section>
  );
}
