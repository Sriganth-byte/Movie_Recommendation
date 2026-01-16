import { useState } from "react";
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
];

const MOODS = ["Fast", "Emotional", "Dark", "Light"];

export default function PersonalRecoModal({ open, onClose, onSubmit }) {
  const [movie, setMovie] = useState("");
  const [genres, setGenres] = useState([]);
  const [rating, setRating] = useState(7);
  const [mood, setMood] = useState("");
  const [yearFrom, setYearFrom] = useState(2000);
  const [yearTo, setYearTo] = useState(new Date().getFullYear());

  if (!open) return null;

  function toggle(list, value, setter) {
    setter(
      list.includes(value)
        ? list.filter((v) => v !== value)
        : [...list, value]
    );
  }

  function submit() {
    onSubmit({
      movie,
      genres,
      rating,
      mood,
      yearFrom,
      yearTo,
    });
    onClose();
  }

  return (
    <div className="modal-backdrop">
      <div className="modal slide-in">
        <h2>🎯 Personalized Picks</h2>

        {/* REFERENCE MOVIE */}
        <label>Recently watched / favorite movie</label>
        <input
          value={movie}
          onChange={(e) => setMovie(e.target.value)}
          placeholder="Interstellar, Joker, Dune..."
        />

        {/* GENRES */}
        <label>Preferred genres</label>
        <div className="chips">
          {GENRES.map((g) => (
            <span
              key={g}
              className={genres.includes(g) ? "chip active" : "chip"}
              onClick={() => toggle(genres, g, setGenres)}
            >
              {g}
            </span>
          ))}
        </div>

        {/* YEAR RANGE */}
        <label>Release year range</label>
        <div className="year-range">
          <input
            type="number"
            min="1950"
            max={yearTo}
            value={yearFrom}
            onChange={(e) => setYearFrom(Number(e.target.value))}
          />
          <span>to</span>
          <input
            type="number"
            min={yearFrom}
            max={new Date().getFullYear()}
            value={yearTo}
            onChange={(e) => setYearTo(Number(e.target.value))}
          />
        </div>

        {/* RATING */}
        <label>Minimum IMDb rating: {rating}+</label>
        <input
          type="range"
          min="5"
          max="9"
          step="0.5"
          value={rating}
          onChange={(e) => setRating(Number(e.target.value))}
        />

        {/* MOOD */}
        <label>Mood</label>
        <div className="chips">
          {MOODS.map((m) => (
            <span
              key={m}
              className={mood === m ? "chip active" : "chip"}
              onClick={() => setMood(m)}
            >
              {m}
            </span>
          ))}
        </div>

        {/* ACTIONS */}
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
