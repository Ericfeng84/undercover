import { useEffect, useState } from "react";
import { fetchInstructions } from "./api";
import { errorMessage } from "./format";
import { Panel } from "./Panel";

export function InstructionsPage() {
  const [instructions, setInstructions] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const text = await fetchInstructions();
        if (active) {
          setInstructions(text);
        }
      } catch (loadError) {
        if (active) {
          setError(errorMessage(loadError));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return <p className="muted">Loading instructions...</p>;
  }

  if (error) {
    return (
      <div className="error" role="alert">
        {error}
      </div>
    );
  }

  return (
    <Panel title="UnderCover Agent instructions">
      <pre className="instructions-text">{instructions}</pre>
    </Panel>
  );
}
