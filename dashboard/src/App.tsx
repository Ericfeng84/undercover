import { useState } from "react";
import { ClaimPage } from "./ClaimPage";
import { Header } from "./Header";
import { QueuePage } from "./QueuePage";
import type { View } from "./types";

export function App() {
  const [view, setView] = useState<View>({ kind: "queue" });

  return (
    <div className="app">
      <Header
        onQueue={() => {
          setView({ kind: "queue" });
        }}
      />
      <main className="page">
        {view.kind === "queue" && (
          <QueuePage
            onOpenClaim={(claimId) => {
              setView({ kind: "claim", claimId });
            }}
          />
        )}
        {view.kind === "claim" && (
          <ClaimPage
            key={view.claimId}
            claimId={view.claimId}
            onBack={() => {
              setView({ kind: "queue" });
            }}
          />
        )}
      </main>
    </div>
  );
}
