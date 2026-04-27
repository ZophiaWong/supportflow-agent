import { NavLink, Outlet } from "react-router-dom";

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="app-header__eyebrow">AI support workflow demo</p>
          <h1>Support Agent Demo</h1>
          <p className="app-header__description">
            Scan support queues, run the LangGraph workflow, and review risky AI drafts.
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
              Inbox
            </NavLink>
            <NavLink
              className={({ isActive }) =>
                `app-sidebar__link ${isActive ? "app-sidebar__link--active" : ""}`
              }
              to="/reviews"
            >
              Review Queue
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
