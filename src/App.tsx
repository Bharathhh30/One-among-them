import type { CSSProperties, FormEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

type Character = { id: string; name: string; image: string };
type DumpCharacter = Character & { x: number; y: number; size: number; rotation: number; z: number; radius: string };
type Classification = { categories: { id: string; probability: number }[]; characters: string[]; source: string; mode?: string };
type Flight = Character & { left: number; top: number; width: number; dx: number; dy: number; rotation: number };
const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

const characters: Character[] = [
  ["nobita", "Nobita", "nobita.png"], ["naruto", "Naruto", "naruto.png"], ["spider-man", "Spider-Man", "spiderman.png"],
  ["salman-khan", "Salman Khan", "salman-khan.png"], ["salman-khan-ceo", "Salman Khan CEO", "salman-khan-ceo.png"], ["salman-khan-sad", "Salman Khan Sad", "salman-khan-sad.png"],
  ["dhurandar", "Dhurandhar", "dhurandar.png"], ["ajit-doval", "Ajit Doval", "ajit-sanyal.png"],
  ["elon-musk", "Elon Musk", "elon.png"], ["ishowspeed", "IShowSpeed", "speed.png"], ["speed-hmmm", "Speed Hmmm", "speed-hmmm.png"], ["loki", "Loki", "loki.png"],
  ["srk", "SRK", "rajni.png"], ["max-verstappen", "Max Verstappen", "max.png"], ["pr", "PR", "PR.png"],
  ["uzair-baloch", "Uzair Baloch", "uzair.png"], ["mufasa", "Mufasa", "mufasa.png"], ["rajinikanth", "Rajinikanth", "rajni-swag.png"],
  ["lewis-hamilton", "Lewis Hamilton", "lewis.png"], ["peter-parker", "Peter Parker", "peter-parker.png"],
  ["suzuka", "Suzuka", "suzuka.png"], ["arjun", "Arjun", "arjun.png"], ["arjun-trying", "Arjun Trying", "arjun-trying.png"],
  ["jd", "JD", "jd.png"], ["jd-sad", "JD Sad", "jd-sad.png"], ["anuskha-sharma", "Anushka Sharma", "anuskha-sharma.png"],
  ["barfi", "Barfi", "Barfi.png"], ["doreamon-acha-loude", "Doreamon", "doreamon-acha-loude.png"], ["leo-das", "Leo Das", "leo-das.png"],
  ["parthiban", "Parthiban", "parthiban.png"],
].map(([id, name, file]) => ({ id, name, image: `/one-among-them/${file}` }))
  // One physical image may only occupy one place in the dump.
  .filter((character, index, all) => all.findIndex((item) => item.image === character.image) === index);

const positions: [number, number, number, number, number, string][] = [
  [0, 58, 122, -18, 1, "0"], [5, 43, 135, 12, 2, "0"], [11, 63, 145, 178, 3, "0"],
  [17, 36, 118, -8, 4, "0"], [23, 54, 155, 22, 5, "0"], [29, 41, 126, -170, 6, "0"],
  [35, 64, 136, 9, 7, "0"], [41, 48, 148, 188, 8, "0"], [47, 59, 120, -26, 9, "0"],
  [53, 35, 150, 14, 10, "0"], [59, 62, 132, -185, 11, "0"], [65, 45, 158, 31, 12, "0"],
  [71, 58, 126, -12, 13, "0"], [77, 37, 145, 168, 14, "0"], [83, 61, 150, -24, 15, "0"],
  [88, 47, 118, 8, 16, "0"], [13, 73, 140, 195, 17, "0"], [43, 72, 130, -14, 18, "0"],
];

function positionFor(index: number): Omit<DumpCharacter, keyof Character> {
  const columns = 8;
  const column = index % columns;
  const row = Math.floor(index / columns);
  const rotations = [-18, 12, 178, -8, 22, -170, 9, 188, -26, 14, -185, 31, -12, 168, -24, 8, 195, -14];
  const size = 112 + ((index * 29) % 46);
  const y = 22 + row * 18 + ((index * 7) % 7) - 3;
  const x = column * 12 + (row % 2 ? 2 : 0) - 2;
  return { x, y, size, rotation: rotations[index % rotations.length], z: index + 1, radius: "0" };
}

const dumpCharacters: DumpCharacter[] = characters.map((character, index) => {
  const { x, y, size, rotation, z, radius } = positionFor(index);
  return { ...character, x, y, size, rotation, z, radius };
});

function App() {
  const [input, setInput] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [arrived, setArrived] = useState(false);
  const [flights, setFlights] = useState<Flight[]>([]);
  const [flightMoving, setFlightMoving] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("the pile is listening");
  const [showAudioButton, setShowAudioButton] = useState(false);
  const [mode, setMode] = useState<string | undefined>();
  const resultRef = useRef<HTMLElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (!flights.length) return;
    setFlightMoving(false);
    const frame = window.requestAnimationFrame(() => setFlightMoving(true));
    return () => window.cancelAnimationFrame(frame);
  }, [flights]);

  const selectedCharacters = useMemo(
    () => selected.map((id) => characters.find((character) => character.id === id)).filter(Boolean) as Character[],
    [selected],
  );

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!input.trim() || loading) return;
    setLoading(true);
    setSubmitted(true);
    setSelected([]);
    setArrived(false);
    setShowAudioButton(false);
    setMode(undefined);
    audioRef.current?.pause();
    if (audioRef.current) audioRef.current.currentTime = 0;
    await new Promise((resolve) => setTimeout(resolve, 420));
    try {
      const response = await fetch(`${API_URL}/api/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input }),
      });
      const data = (await response.json()) as Classification | { error: string };
      if (!response.ok || !("characters" in data)) throw new Error("error" in data ? data.error : "Could not read that.");
      setMode(data.mode);
      setStatus(`${data.source} · ${data.categories[0]?.id.replaceAll("_", " ") || "interesting"} energy`);
      const selectedIds = data.characters.slice(0, 5);
      if (data.mode === "one_sided_love") {
        audioRef.current?.play().catch(() => {
          setShowAudioButton(true);
          setStatus("tap again to play the one-sided-love audio");
        });
      }
      const resultTop = resultRef.current?.getBoundingClientRect().top ?? 0;
      const imageWidth = Math.min(160, Math.max(105, window.innerWidth * 0.14));
      const gap = Math.min(34, Math.max(10, window.innerWidth * 0.03));
      const totalWidth = imageWidth * selectedIds.length + gap * (selectedIds.length - 1);
      const startX = (window.innerWidth - totalWidth) / 2;
      const nextFlights = selectedIds.flatMap((id, index) => {
        const source = document.querySelector<HTMLButtonElement>(`.dump-item[data-character="${id}"]`);
        const character = characters.find((item) => item.id === id);
        if (!source || !character) return [];
        const rect = source.getBoundingClientRect();
        return [{
          ...character,
          left: rect.left,
          top: rect.top,
          width: rect.width,
          dx: startX + index * (imageWidth + gap) - rect.left,
          dy: resultTop + 64 - rect.top,
          rotation: index % 2 ? 4 : -4,
        }];
      });
      setSelected(selectedIds);
      setFlights(nextFlights);
    } catch (error) {
      setSubmitted(false);
      setStatus(error instanceof Error ? error.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setSubmitted(false);
    setSelected([]);
    setArrived(false);
    setFlights([]);
    setFlightMoving(false);
    setShowAudioButton(false);
    setMode(undefined);
    audioRef.current?.pause();
    if (audioRef.current) audioRef.current.currentTime = 0;
    setInput("");
    setStatus("the pile is listening");
  }

  return (
    <main className="app-shell">
      <header className="masthead">
        <span className="eyebrow">a tiny experiment using system one model</span>
        <h1>You are <em>1</em> among them<span className="spark">✳</span></h1>
        <p className="intro">Tell us what’s going on in your head. We’ll look through the pile.</p>
      </header>
      <form className="prompt-form" onSubmit={handleSubmit}>
        <label htmlFor="prompt">what’s your current state?</label>
        <div className="input-wrap">
          <textarea
            id="prompt"
            rows={2}
            maxLength={240}
            value={input}
            onChange={(event) => {
              setInput(event.target.value);
              audioRef.current?.pause();
            }}
            placeholder="i feel like doing mischievous things with time"
            required
          />
          <button type="submit" disabled={loading}><span>{loading ? "looking..." : "find my people"}</span><b>↗</b></button>
        </div>
        <div className="form-meta"><span>{status}</span><span>{input.length} / 240</span></div>
      </form>
      <section ref={resultRef} className={`result ${submitted ? "visible" : ""}`} aria-hidden={!submitted}>
        <div className="result-heading">
          <span className="eyebrow">your little constellation</span>
          <h2>
            {mode === "one_sided_love" ? "So your life is dude" : "So you are one among them"}
            <span>....</span>
          </h2>
          <button className="reset" onClick={reset} type="button">try another ↻</button>
          {showAudioButton && (
            <button className="audio-trigger" onClick={() => audioRef.current?.play()} type="button">
              play the feeling ♫
            </button>
          )}
        </div>
        <div className="result-characters">
          {arrived && selectedCharacters.map((character, index) => (
            <div className="result-card" style={{ animationDelay: `${index * 80}ms` }} key={`${character.id}-${index}`}>
              <img src={character.image} alt={character.name} />
              <span>{character.name}</span>
            </div>
          ))}
        </div>
        {mode === "one_sided_love" && (
          <p className="music-note">
            listen to this music and get more depressed now — dude is a generational album
          </p>
        )}
      </section>
      <section className="dump-section">
        <div className="dump-label"><span>the character dump</span><span className="line" /><span>{characters.length} possibilities</span></div>
        <div className="dump" aria-label="A chaotic dump of characters">
          {dumpCharacters.map((character) => {
            const isSelected = selected.includes(character.id);
            return (
              <button
                className={`dump-item ${isSelected ? "extracted" : ""}`}
                data-character={character.id}
                key={character.id}
                type="button"
                aria-label={character.name}
                style={{ "--x": `${character.x}%`, "--y": `${character.y}%`, "--size": `${character.size}px`, "--rotation": `${character.rotation}deg`, "--z": character.z, "--radius": character.radius } as CSSProperties}
              >
                <img src={character.image} alt={character.name} draggable={false} />
              </button>
            );
          })}
        </div>
      </section>
      <audio ref={audioRef} src="/audio/dude-ochestral-suite.mp3" preload="auto" />
      {flights.map((flight, index) => (
        <img
          className={`flight-image ${flightMoving ? "moving" : ""}`}
          key={flight.id}
          src={flight.image}
          alt=""
          aria-hidden="true"
          onTransitionEnd={(event) => {
            if (index === flights.length - 1 && event.propertyName === "transform") {
              setFlights([]);
              setArrived(true);
            }
          }}
          style={{
            left: flight.left,
            top: flight.top,
            width: flight.width,
            "--dx": `${flight.dx}px`,
            "--dy": `${flight.dy}px`,
            "--flight-rotation": `${flight.rotation}deg`,
          } as CSSProperties}
        />
      ))}
    </main>
  );
}

export default App;
