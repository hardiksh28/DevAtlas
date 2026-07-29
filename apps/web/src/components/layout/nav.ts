import {
  BookOpen,
  FileText,
  FolderKanban,
  GitPullRequest,
  LayoutDashboard,
  Map,
  MessageSquare,
  Settings,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  icon: LucideIcon;
  /** Present only for live routes — "coming soon" items have no href
   * and render as non-interactive so nothing looks clickable that isn't. */
  href?: string;
}

export interface NavSection {
  label: string;
  items: NavItem[];
}

// One nav definition shared by the desktop sidebar and the mobile
// drawer so the two can never drift. Items without an href are future
// modules (no backend yet) — shown so the product's shape is visible,
// marked "Soon", and not clickable.
export const NAV_SECTIONS: NavSection[] = [
  {
    label: "Workspace",
    items: [
      { label: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
      { label: "Projects", icon: FolderKanban, href: "/projects" },
    ],
  },
  {
    label: "Learning",
    items: [
      { label: "Roadmap", icon: Map },
      { label: "Lessons", icon: BookOpen },
      { label: "Progress", icon: TrendingUp },
    ],
  },
  {
    label: "Build",
    items: [
      { label: "Documentation", icon: FileText },
      { label: "Mentor", icon: MessageSquare },
      { label: "Code Review", icon: GitPullRequest },
    ],
  },
];

export const SETTINGS_ITEM: NavItem = { label: "Settings", icon: Settings, href: "/settings" };
