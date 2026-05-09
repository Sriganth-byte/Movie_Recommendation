import { useEffect, useRef, useState } from "react";
import "../styles/recoModal.css";

const GENRES = [
  "Action",
  "Drama",
  "Comedy",
  "Horror",
  "Romance",
  "Sci-Fi",
  "Thriller",
  "Adventure",
  "Mystery",
  "Crime",
  "Family",
  "Animation",
];

const MOODS = ["Fast", "Emotional", "Dark", "Light"];
const CURRENT_YEAR = new Date().getFullYear();

export default function PersonalRecoModal({ open, metadata, onClose, onSubmit }) {
  const availableGenres = metadata?.genres?.length ? metadata.genres.slice(0, 16) : GENRES;
  const availableMoods = metadata?.moods?.length ? metadata.moods : MOODS;
  const yearMin = metadata?.yearMin || 1900;
  const yearMax = metadata?.yearMax || CURRENT_YEAR;
  const [movie, setMovie] = useState("");
  const [genres, setGenres] = useState([]);
  const [rating, setRating] = useState(7);
  const [mood, setMood] = useState("");
  const [yearFrom, setYearFrom] = useState(2000);
  const [yearTo, setYearTo] = useState(yearMax);
  const firstFocusRef = useRef(null);

  useEffect(() => {
    setYearFrom((current) => Math.max(yearMin, Math.min(current, yearMax)));
    setYearTo((current) => Math.max(yearMin, Math.min(current, yearMax)));
  }, [yearMin, yearMax]);

  // Focus first input and handle Escape key when modal opens
  useEffect(() => {
    if (!open) return;
    firstFocusRef.current?.focus();
    function handleKeyDown(e) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  function toggleGenre(value) {
    setGenres((current) =>
      current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value]
    );
  }

  function submit() {
    const from = Math.min(yearFrom, yearTo);
    const to = Math.max(yearFrom, yearTo);
    onSubmit({ movie: movie.trim(), genres, rating, mood, yearFrom: from, yearTo: to });
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <div
        className="modal slide-in"
        role="dialog"
        aria-modal="true"
        aria-labelledby="reco-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h2 id="reco-title">Personalized Picks</h2>

        <label htmlFor="favorite-movie">Recently watched or favorite movie</label>
        <input
          ref={firstFocusRef}
          id="favorite-movie"
          value={movie}
          onChange={(e) => setMovie(e.target.value)}
          placeholder="Interstellar, Joker, Dune..."
        />

        <label id="genres-label">Preferred genres</label>
        <div className="chips" role="group" aria-labelledby="genres-label">
          {availableGenres.map((g) => (
            <button
              type="button"
              key={g}
              className={genres.includes(g) ? "chip active" : "chip"}
              aria-pressed={genres.includes(g)}
              onClick={() => toggleGenre(g)}
            >
              {g}
            </button>
          ))}
        </div>

        <label id="year-range-label">Release year range</label>
        <div className="year-range" role="group" aria-labelledby="year-range-label">
          <input
            type="number"
            aria-label="Year from"
            min={yearMin}
            max={yearTo}
            value={yearFrom}
            onChange={(e) => setYearFrom(Number(e.target.value))}
          />
          <span aria-hidden="true">to</span>
          <input
            type="number"
            aria-label="Year to"
            min={yearFrom}
            max={yearMax}
            value={yearTo}
            onChange={(e) => setYearTo(Number(e.target.value))}
          />
        </div>

        <label htmlFor="minimum-rating">Minimum rating: {rating}+</label>
        <input
          id="minimum-rating"
          type="range"
          min="5"
          max="9"
          step="0.5"
          value={rating}
          onChange={(e) => setRating(Number(e.target.value))}
        />

        <label id="mood-label">Mood</label>
        <div className="chips" role="group" aria-labelledby="mood-label">
          {availableMoods.map((m) => (
            <button
              type="button"
              key={m}
              className={mood === m ? "chip active" : "chip"}
              aria-pressed={mood === m}
              onClick={() => setMood((current) => (current === m ? "" : m))}
            >
              {m}
            </button>
          ))}
        </div>

        <button className="primary" onClick={submit}>
          Get Recommendations
        </button>

        <button className="secondary" onClick={onClose}>
          Cancel
        </button>
      </div>
    </div>
  );
}
