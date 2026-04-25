import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ReviewQueuePage } from "./pages/ReviewQueuePage";
import { TicketsPage } from "./pages/TicketsPage";
import "./styles.css";

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate replace to="/tickets" />} />
        <Route path="/tickets" element={<TicketsPage />} />
        <Route path="/reviews" element={<ReviewQueuePage />} />
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>,
);
