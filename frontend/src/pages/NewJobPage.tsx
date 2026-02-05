import { useNavigate } from "react-router-dom";
import NewJDWizard from "../components/NewJDWizard";

export default function NewJobPage() {
  const navigate = useNavigate();

  return (
    <div>
      <NewJDWizard
        open={true}
        onClose={() => navigate("/jobs")}
      />
    </div>
  );
}
