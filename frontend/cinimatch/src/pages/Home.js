import { useEffect, useState } from "react";

import Navbar from "../components/Navbar";
import HallOfFame from "../components/HallOfFame";
import MovieDetails from "../components/MovieDetail";
import MovieRow from "../components/MovieRow";
import PersonalRecoModal from "../components/PersonalRecoModal";

import {
  getTopPicks,
  getPersonalRecommendations,
} from "../services/api";

export default function Home() {
  const [topPicks, setTopPicks] = useState([]);
  const [selectedMovie, setSelectedMovie] = useState(null);

  const [openReco, setOpenReco] = useState(false);
  const [recoInput, setRecoInput] = useState(null);

  /* ================= INITIAL LOAD ================= */
  useEffect(() => {
    getTopPicks().then((data) => {
      setTopPicks(data || []);
      setSelectedMovie(data?.[0] || null);
    });
  }, []);

  /* ================= MOVIE SELECTION ================= */
  function handleSelect(movie) {
    if (!movie) return;

    // reset personal recommendations when user manually selects
    setRecoInput(null);
    setSelectedMovie(movie);
  }

  /* ================= OPEN RECO MODAL ================= */
  function openRecommendationModal() {
    // clear previous recommendation results
    setRecoInput(null);
    setOpenReco(true);
  }

  return (
    <>
      <Navbar
        onSelect={handleSelect}
        onOpenReco={openRecommendationModal}
      />

      <HallOfFame
        movies={topPicks}
        onSelect={handleSelect}
      />

      <MovieDetails
      movie={selectedMovie}
      onSelect={handleSelect}
    />


      {/* ================= PERSONAL RECOMMENDATIONS ================= */}
      {recoInput && (
        <MovieRow
          title="Recommended For You"
          autoLoad={true}
          fetchMore={(offset, limit) =>
            getPersonalRecommendations(
              recoInput,
              offset,
              limit
            )
          }
          onSelect={handleSelect}
        />
      )}

      {/* ================= TRENDING ================= */}
      <MovieRow
        title="Trending"
        fetchType="trending"
        onSelect={handleSelect}
      />

      {/* ================= GENRES ================= */}
      {["Action", "Drama", "Comedy", "Horror", "Romance"].map((g) => (
        <MovieRow
          key={g}
          title={g}
          genre={g}
          fetchType="genre"
          onSelect={handleSelect}
        />
      ))}

      {/* ================= MODAL ================= */}
      <PersonalRecoModal
        open={openReco}
        onClose={() => setOpenReco(false)}
        onSubmit={(data) => {
          setRecoInput(data);
          setOpenReco(false);
        }}
      />
    </>
  );
}
