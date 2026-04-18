import Editor from "@monaco-editor/react";

interface Props {
  label: string;
  identifier: string;
  onIdentifierChange: (v: string) => void;
  value: string;
  onChange: (v: string) => void;
}

export function EditorPane({
  label,
  identifier,
  onIdentifierChange,
  value,
  onChange,
}: Props) {
  return (
    <div className="editor-pane">
      <div className="pane-header">
        <span>{label}</span>
        <input
          type="text"
          value={identifier}
          placeholder="identifier"
          onChange={(e) => onIdentifierChange(e.target.value)}
        />
      </div>
      <div className="editor-host">
        <Editor
          language="json"
          theme="vs-dark"
          value={value}
          onChange={(v) => onChange(v ?? "")}
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            wordWrap: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
}
