interface HeaderProps {
  onQueue: () => void;
  onInstructions: () => void;
}

export function Header({ onQueue, onInstructions }: Readonly<HeaderProps>) {
  return (
    <header className="site-header">
      <button type="button" className="brand" onClick={onQueue}>
        <span className="brand-name">UnderCover</span>
        <span className="tagline">Travel claims, decided with care</span>
      </button>
      <nav className="main-nav" aria-label="Main">
        <button type="button" className="nav-button" onClick={onQueue}>
          Queue
        </button>
        <button type="button" className="nav-button" onClick={onInstructions}>
          Instructions
        </button>
      </nav>
    </header>
  );
}
