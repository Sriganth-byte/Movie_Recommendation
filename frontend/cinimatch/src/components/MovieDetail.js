import { useEffect, useState } from "react";
import { getCredits, getSimilarMovies } from "../services/api";
import MovieCard from "./MovieCard";
import "../styles/movieDetail.css";

function normalizeGenres(genres) {
  if (!genres) return [];
  if (Array.isArray(genres)) return genres.slice(0, 4);
  if (typeof genres === "string")
    return genres.split(",").map((g) => g.trim()).slice(0, 4);
  return [];
}

export default function MovieDetails({ movie, onSelect }) {
  const [cast, setCast] = useState([]);
  const [similar, setSimilar] = useState([]);
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    if (!movie?.imdb_id) return;

    setAnimate(false);

    getCredits(movie.imdb_id).then((c) =>
      setCast(Array.isArray(c?.cast) ? c.cast : [])
    );

    getSimilarMovies(movie.imdb_id).then((s) => {
      setSimilar(Array.isArray(s) ? s.slice(0, 7) : []);
      setTimeout(() => setAnimate(true), 100);
    });
  }, [movie?.imdb_id]);

  if (!movie) return null;

  const genres = normalizeGenres(movie.genres);

  return (
  <section className="details">
    {/* TOP LAYOUT */}
    <div className="details-layout">
      
      {/* POSTER */}
      <div className="details-poster">
        <img
          src={
            movie.poster_path
              ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
              : "/placeholder.jpg"
          }
          alt={movie.title}
        />
      </div>

      {/* META DATA */}
      <div className="details-meta">
        <h1>{movie.title}</h1>

        <div className="header-stats">
          <span className="rating">⭐ {movie.vote_average}</span>
          <span>{movie.vote_count} votes</span>
          <span>🔥 {Math.round(movie.popularity)}</span>

          {genres.map((g, i) => (
            <span key={i} className="genre-chip">{g}</span>
          ))}
        </div>

        <p className="overview">
          {movie.overview || "No description available."}
        </p>

        {/* CAST */}
        {cast.length > 0 && (
          <div className="cast">
            <h3>Cast</h3>
            <div className="cast-list">
              {cast.slice(0, 6).map((c, i) => (
                <span key={i}>{c.name}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>

    {/* SIMILAR MOVIES — FULL WIDTH BELOW */}
    {similar.length > 0 && (
      <div className="similar-section">
        <h3>More Like This</h3>

        <div className={`similar-row ${animate ? "show" : ""}`}>
          {similar.map((m, i) => (
            <div
              key={m.imdb_id}
              className="similar-item"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <MovieCard movie={m} onClick={onSelect} />
            </div>
          ))}
        </div>
      </div>
    )}
  </section>
);
}
