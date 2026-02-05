import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ExpandableTextarea from "./ExpandableTextarea";

describe("ExpandableTextarea", () => {
  it("renders with initial value", () => {
    render(
      <ExpandableTextarea value="Test content" onChange={() => {}} />
    );
    expect(screen.getByRole("textbox")).toHaveValue("Test content");
  });

  it("calls onChange when text is entered", () => {
    const handleChange = vi.fn();
    render(<ExpandableTextarea value="" onChange={handleChange} />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "New text" } });

    expect(handleChange).toHaveBeenCalledWith("New text");
  });

  it("shows placeholder text", () => {
    render(
      <ExpandableTextarea
        value=""
        onChange={() => {}}
        placeholder="Enter text here..."
      />
    );
    expect(screen.getByPlaceholderText("Enter text here...")).toBeInTheDocument();
  });

  it("can be disabled", () => {
    render(
      <ExpandableTextarea value="Test" onChange={() => {}} disabled />
    );
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("can be read-only", () => {
    render(
      <ExpandableTextarea value="Test" onChange={() => {}} readOnly />
    );
    expect(screen.getByRole("textbox")).toHaveAttribute("readonly");
  });

  it("calls onBlur when focus is lost", () => {
    const handleBlur = vi.fn();
    render(
      <ExpandableTextarea value="Test" onChange={() => {}} onBlur={handleBlur} />
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.focus(textarea);
    fireEvent.blur(textarea);

    expect(handleBlur).toHaveBeenCalled();
  });
});
