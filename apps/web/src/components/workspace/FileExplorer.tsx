"use client";

import { File, FilePlus, Folder, Pencil, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import {
  useCreateWorkspaceFile,
  useDeleteWorkspaceFile,
  useRenameWorkspaceFile,
  useWorkspaceTree,
} from "@/hooks/useWorkspace";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import type { WorkspaceFileMeta } from "@/types/workspace";

interface TreeNode {
  name: string;
  path: string;
  type: "file" | "folder";
  fileId?: string;
  children?: TreeNode[];
}

// Folders are derived from flat file paths at render time — there is no
// folder row in the backend at all (see workspace/models.py's docstring
// on why). Same approach a git tree view takes.
function buildTree(files: WorkspaceFileMeta[]): TreeNode[] {
  const root: TreeNode[] = [];
  for (const file of files) {
    const segments = file.path.split("/");
    let level = root;
    let currentPath = "";
    segments.forEach((segment, index) => {
      currentPath = currentPath ? `${currentPath}/${segment}` : segment;
      const isFile = index === segments.length - 1;
      let node = level.find((n) => n.name === segment && n.type === (isFile ? "file" : "folder"));
      if (!node) {
        node = isFile
          ? { name: segment, path: currentPath, type: "file", fileId: file.id }
          : { name: segment, path: currentPath, type: "folder", children: [] };
        level.push(node);
      }
      if (!isFile) level = node.children!;
    });
  }
  const sortRec = (nodes: TreeNode[]) => {
    nodes.sort((a, b) =>
      a.type !== b.type ? (a.type === "folder" ? -1 : 1) : a.name.localeCompare(b.name),
    );
    nodes.forEach((n) => n.children && sortRec(n.children));
  };
  sortRec(root);
  return root;
}

function TreeRow({
  node,
  depth,
  onOpen,
  onRename,
  onDelete,
}: {
  node: TreeNode;
  depth: number;
  onOpen: (fileId: string) => void;
  onRename: (fileId: string, path: string) => void;
  onDelete: (fileId: string, path: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const paddingLeft = 8 + depth * 14;

  if (node.type === "folder") {
    return (
      <div>
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="flex w-full items-center gap-1.5 rounded-sm px-2 py-1 text-left text-sm text-ink-muted hover:bg-surface-muted hover:text-ink"
          style={{ paddingLeft }}
        >
          <Folder className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span className="truncate">{node.name}</span>
        </button>
        {expanded &&
          node.children?.map((child) => (
            <TreeRow
              key={child.path}
              node={child}
              depth={depth + 1}
              onOpen={onOpen}
              onRename={onRename}
              onDelete={onDelete}
            />
          ))}
      </div>
    );
  }

  return (
    <div
      className="group flex items-center gap-1 rounded-sm pr-1 text-sm text-ink-muted hover:bg-surface-muted hover:text-ink"
      style={{ paddingLeft }}
    >
      <button
        type="button"
        onClick={() => onOpen(node.fileId as string)}
        className="flex min-w-0 flex-1 items-center gap-1.5 py-1 text-left"
      >
        <File className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        <span className="truncate">{node.name}</span>
      </button>
      <button
        type="button"
        onClick={() => onRename(node.fileId as string, node.path)}
        aria-label={`Rename ${node.path}`}
        className="rounded-sm p-1 opacity-0 hover:bg-surface hover:text-ink group-hover:opacity-100"
      >
        <Pencil className="h-3 w-3" />
      </button>
      <button
        type="button"
        onClick={() => onDelete(node.fileId as string, node.path)}
        aria-label={`Delete ${node.path}`}
        className="rounded-sm p-1 opacity-0 hover:bg-surface hover:text-danger-ink group-hover:opacity-100"
      >
        <Trash2 className="h-3 w-3" />
      </button>
    </div>
  );
}

export function FileExplorer({ projectId }: { projectId: string }) {
  const { data: tree, isLoading } = useWorkspaceTree(projectId);
  const createFile = useCreateWorkspaceFile(projectId);
  const renameFile = useRenameWorkspaceFile(projectId);
  const deleteFile = useDeleteWorkspaceFile(projectId);
  const openTab = useWorkspaceStore((s) => s.openTab);
  const closeTab = useWorkspaceStore((s) => s.closeTab);

  const [newPath, setNewPath] = useState("");
  const [renaming, setRenaming] = useState<{ fileId: string; path: string; value: string } | null>(null);
  const [deleting, setDeleting] = useState<{ fileId: string; path: string } | null>(null);

  const nodes = useMemo(() => buildTree(tree?.items ?? []), [tree]);

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const path = newPath.trim();
    if (!path) return;
    createFile.mutate(
      { path, content: "" },
      {
        onSuccess: (file) => {
          setNewPath("");
          openTab(file.id);
        },
      },
    );
  }

  function commitRename() {
    if (!renaming) return;
    const folder = renaming.path.includes("/")
      ? renaming.path.slice(0, renaming.path.lastIndexOf("/") + 1)
      : "";
    const newFilePath = `${folder}${renaming.value.trim()}`;
    if (newFilePath && newFilePath !== renaming.path) {
      renameFile.mutate({ fileId: renaming.fileId, payload: { new_path: newFilePath } });
    }
    setRenaming(null);
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-line px-2 py-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Files</span>
      </div>
      <form onSubmit={handleCreate} className="flex items-center gap-1 border-b border-line p-2">
        <input
          value={newPath}
          onChange={(e) => setNewPath(e.target.value)}
          placeholder="path/to/file.js"
          className="min-w-0 flex-1 rounded-sm border border-line bg-canvas px-2 py-1 text-xs text-ink placeholder:text-ink-faint focus:border-accent focus:outline-none"
        />
        <button
          type="submit"
          disabled={createFile.isPending || !newPath.trim()}
          aria-label="Create file"
          className="rounded-sm p-1.5 text-ink-muted hover:bg-surface-muted hover:text-ink disabled:opacity-50"
        >
          <FilePlus className="h-4 w-4" />
        </button>
      </form>

      <div className="flex-1 overflow-y-auto py-1">
        {isLoading && <p className="px-3 py-2 text-xs text-ink-muted">Loading files…</p>}
        {!isLoading && nodes.length === 0 && (
          <p className="px-3 py-2 text-xs text-ink-muted">No files yet — create one above.</p>
        )}
        {nodes.map((node) => {
          const activeRename = renaming?.fileId === node.fileId ? renaming : null;
          return activeRename ? (
            <input
              key={node.path}
              autoFocus
              value={activeRename.value}
              onChange={(e) => setRenaming({ ...activeRename, value: e.target.value })}
              onBlur={commitRename}
              onKeyDown={(e) => {
                if (e.key === "Enter") commitRename();
                if (e.key === "Escape") setRenaming(null);
              }}
              className="mx-2 rounded-sm border border-accent bg-canvas px-1.5 py-1 text-sm text-ink focus:outline-none"
            />
          ) : (
            <TreeRow
              key={node.path}
              node={node}
              depth={0}
              onOpen={openTab}
              onRename={(fileId, path) =>
                setRenaming({ fileId, path, value: path.split("/").pop() ?? path })
              }
              onDelete={(fileId, path) => setDeleting({ fileId, path })}
            />
          );
        })}
      </div>

      <ConfirmDialog
        open={deleting !== null}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (!deleting) return;
          const fileId = deleting.fileId;
          deleteFile.mutate(fileId, { onSuccess: () => closeTab(fileId) });
          setDeleting(null);
        }}
        title="Delete file"
        description={deleting ? `"${deleting.path}" will be permanently deleted.` : ""}
        confirmLabel="Delete"
        destructive
        pending={deleteFile.isPending}
      />
    </div>
  );
}
