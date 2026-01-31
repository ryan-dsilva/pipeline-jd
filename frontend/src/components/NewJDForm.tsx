import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createJob } from "../lib/api";
import Button from "./ui/Button";
import Input from "./ui/Input";

export default function NewJDForm() {
  const navigate = useNavigate();
  const [jdUrl, setJdUrl] = useState("");
  const [jdText, setJdText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jdUrl.trim() || !jdText.trim()) {
      setError("Both JD URL and JD text are required.");
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      const job = await createJob({
        jd_url: jdUrl.trim(),
        jd_text: jdText.trim(),
      });
      navigate(`/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-4">
      {error && (
        <div className="text-sm text-error bg-error/5 px-3 py-2 rounded-md border border-error/20">
          {error}
        </div>
      )}

      <div>
        <label
          htmlFor="jd-url"
          className="block text-sm font-medium text-text-primary mb-1"
        >
          JD URL
        </label>
        <Input
          id="jd-url"
          variant="url"
          value={jdUrl}
          onChange={(e) => setJdUrl(e.target.value)}
          className="w-full"
          placeholder="https://boards.greenhouse.io/..."
        />
      </div>

      <div>
        <label
          htmlFor="jd-text"
          className="block text-sm font-medium text-text-primary mb-1"
        >
          JD Text
        </label>
        <p className="text-xs text-text-secondary mb-2">
          Copy and paste the full job posting — we'll extract the details
        </p>
        <Input
          id="jd-text"
          variant="textarea"
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
          rows={12}
          className="w-full font-mono"
          placeholder="Paste the full job description here..."
        />
      </div>

      <Button type="submit" disabled={submitting}>
        {submitting ? "Creating..." : "Create Job"}
      </Button>
    </form>
  );
}
