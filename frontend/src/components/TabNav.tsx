import { Link, useLocation } from "react-router-dom";
import Button from "./ui/Button";

export default function TabNav() {
  const { pathname } = useLocation();
  const isDetail = pathname.startsWith("/jobs/");

  return (
    <nav className="border-b border-border-light bg-white shadow-sm px-6">
      <div className="flex items-center justify-between h-14">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2">
            <span className="font-semibold text-lg text-text-primary">
              Pipeline
            </span>
            {!isDetail && (
              <span className="text-sm text-text-secondary hidden sm:inline">
                Job analysis, automated.
              </span>
            )}
          </Link>
        </div>
        <Link to="/new">
          <Button size="sm">+ New Job</Button>
        </Link>
      </div>
    </nav>
  );
}
