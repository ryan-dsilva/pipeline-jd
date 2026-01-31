import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import TabNav from "./components/TabNav";
import JobsPage from "./pages/JobsPage";
import NewJobPage from "./pages/NewJobPage";
import RoleDetailPage from "./pages/RoleDetailPage";

function ListLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg-cream flex flex-col">
      <TabNav />
      <main className="flex-1 px-6 py-6">{children}</main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Detail page has its own full-screen layout */}
        <Route path="/jobs/:id" element={<RoleDetailPage />} />

        {/* List pages share TabNav header */}
        <Route
          path="/"
          element={
            <ListLayout>
              <JobsPage />
            </ListLayout>
          }
        />
        <Route
          path="/new"
          element={
            <ListLayout>
              <NewJobPage />
            </ListLayout>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
