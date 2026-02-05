import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Link from "@tiptap/extension-link";
import { Markdown } from "tiptap-markdown";
import { useEffect } from "react";

interface Props {
  content: string;
  onChange: (md: string) => void;
  editable?: boolean;
}

export default function SectionEditor({
  content,
  onChange,
  editable = true,
}: Props) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({ openOnClick: false }),
      Markdown,
    ],
    content,
    editable,
    onUpdate: ({ editor }) => {
      onChange((editor.storage as any).markdown.getMarkdown());
    },
  });

  useEffect(() => {
    if (editor && !editor.isFocused) {
      const current = (editor.storage as any).markdown.getMarkdown();
      if (current.trim() !== content.trim()) {
        editor.commands.setContent(content);
      }
    }
  }, [content, editor]);

  if (!editor) return null;

  return (
    <div className="border border-border-light rounded-md overflow-hidden">
      {editable && (
        <div className="flex gap-0.5 border-b border-border-light p-1.5 bg-off-white">
          <ToolbarBtn
            active={editor.isActive("bold")}
            onClick={() => editor.chain().focus().toggleBold().run()}
            label="B"
            className="font-bold"
          />
          <ToolbarBtn
            active={editor.isActive("italic")}
            onClick={() => editor.chain().focus().toggleItalic().run()}
            label="I"
            className="italic"
          />
          <ToolbarBtn
            active={editor.isActive("bulletList")}
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            label="List"
          />
          <ToolbarBtn
            active={editor.isActive("orderedList")}
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            label="1."
          />
          <ToolbarBtn
            active={editor.isActive("heading", { level: 2 })}
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 2 }).run()
            }
            label="H2"
          />
          <ToolbarBtn
            active={editor.isActive("heading", { level: 3 })}
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 3 }).run()
            }
            label="H3"
          />
        </div>
      )}
      <EditorContent
        editor={editor}
        className="prose prose-sm max-w-none p-3 min-h-[100px] focus:outline-none [&_li_p]:m-0 [&_p]:my-1.5 [&_ul]:my-2 [&_ol]:my-2"
      />
    </div>
  );
}

function ToolbarBtn({
  active,
  onClick,
  label,
  className = "",
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-2 py-1 text-xs rounded ${
        active
          ? "bg-brand-primary/10 text-brand-primary"
          : "text-text-body hover:bg-cream"
      } ${className}`}
    >
      {label}
    </button>
  );
}