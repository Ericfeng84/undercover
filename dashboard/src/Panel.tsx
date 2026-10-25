import type { ReactNode } from "react";

interface PanelProps {
  title: string;
  children: ReactNode;
}

export function Panel({ title, children }: Readonly<PanelProps>) {
  return (
    <section className="panel">
      <h3>{title}</h3>
      {children}
    </section>
  );
}
