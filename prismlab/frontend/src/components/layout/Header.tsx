function Header() {
  return (
    <header className="h-14 bg-bg-secondary border-b border-bg-elevated px-4 flex items-center shrink-0">
      <div className="flex items-center gap-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 32 32"
          className="w-7 h-7"
        >
          <defs>
            <linearGradient id="header-prism" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#00d4ff" />
              <stop offset="50%" stopColor="#6aff97" />
              <stop offset="100%" stopColor="#00d4ff" />
            </linearGradient>
          </defs>
          <path
            d="M16 2 L28 26 L4 26 Z"
            fill="none"
            stroke="url(#header-prism)"
            strokeWidth="2"
          />
          <path
            d="M16 8 L22 22 L10 22 Z"
            fill="url(#header-prism)"
            opacity="0.3"
          />
        </svg>
        <h1 className="text-cyan-accent font-bold text-xl font-body">
          Prismlab
        </h1>
      </div>
    </header>
  );
}

export default Header;
