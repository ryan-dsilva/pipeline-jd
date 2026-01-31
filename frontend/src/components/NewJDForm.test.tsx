import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import NewJDForm from "./NewJDForm";

// Mock useNavigate
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

// Mock API
vi.mock("../lib/api", () => ({
  createJob: vi.fn(),
}));

describe("NewJDForm", () => {
  it("renders only JD URL and JD text inputs", () => {
    render(
      <BrowserRouter>
        <NewJDForm />
      </BrowserRouter>
    );

    // Should have JD URL input
    expect(screen.getByLabelText(/JD URL/i)).toBeInTheDocument();

    // Should have JD Text input
    expect(screen.getByLabelText(/JD Text/i)).toBeInTheDocument();

    // Should NOT have company, role, or date posted inputs
    expect(screen.queryByLabelText(/company/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/role/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/date posted/i)).not.toBeInTheDocument();
  });

  it("shows helper text for JD text input", () => {
    render(
      <BrowserRouter>
        <NewJDForm />
      </BrowserRouter>
    );

    expect(
      screen.getByText(/Copy and paste the full job posting/i)
    ).toBeInTheDocument();
  });

  it("has a submit button", () => {
    render(
      <BrowserRouter>
        <NewJDForm />
      </BrowserRouter>
    );

    const submitButton = screen.getByRole("button", { name: /Create Job/i });
    expect(submitButton).toBeInTheDocument();
    expect(submitButton).not.toBeDisabled();
  });
});
