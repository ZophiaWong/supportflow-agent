import { NavLink, Outlet } from "react-router-dom";

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="app-header__eyebrow">AI support operations</p>
          <h1>SupportFlow Workbench</h1>
          <p className="app-header__description">
            Triage tickets, inspect graph runs, and approve risky AI support actions.
          </p>
        </div>
      </header>

      <div className="app-layout">
        <aside className="app-sidebar" aria-label="Workspace navigation">
          <nav className="app-sidebar__nav">
            <NavLink
              className={({ isActive }) =>
                `app-sidebar__link ${isActive ? "app-sidebar__link--active" : ""}`
              }
              to="/tickets"
            >
              Tickets
            </NavLink>
            <NavLink
              className={({ isActive }) =>
                `app-sidebar__link ${isActive ? "app-sidebar__link--active" : ""}`
              }
              to="/reviews"
            >
              Reviews
            </NavLink>
          </nav>
        </aside>

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
