"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_SECTIONS, SETTINGS_ITEM, type NavItem } from "@/components/layout/nav";

interface SidebarNavProps {
  /** Icon-only rendering for the collapsed desktop sidebar. */
  collapsed?: boolean;
  /** Called after a navigation — the mobile drawer closes itself with this. */
  onNavigate?: () => void;
}

function NavEntry({
  item,
  collapsed,
  onNavigate,
}: {
  item: NavItem;
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const Icon = item.icon;

  if (!item.href) {
    // Future module: visible so the product's direction is clear, but
    // deliberately not a control — nothing here pretends to work.
    return (
      <span
        title={`${item.label} — coming soon`}
        className={`flex min-h-10 items-center gap-3 rounded-md px-3 py-2 text-sm text-ink-faint ${
          collapsed ? "justify-center px-2" : ""
        }`}
      >
        <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
        {!collapsed && (
          <>
            <span className="flex-1">{item.label}</span>
            <span className="rounded border border-line px-1 py-px font-mono text-[10px] uppercase tracking-wide">
              Soon
            </span>
          </>
        )}
      </span>
    );
  }

  const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      title={collapsed ? item.label : undefined}
      aria-current={active ? "page" : undefined}
      className={`flex min-h-10 items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
        collapsed ? "justify-center px-2" : ""
      } ${
        active
          ? "bg-accent-soft text-accent-ink"
          : "text-ink-secondary hover:bg-surface-muted hover:text-ink"
      }`}
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
      {!collapsed && <span>{item.label}</span>}
    </Link>
  );
}

/** The nav list itself — rendered inside both the desktop sidebar and
 * the mobile drawer so the two can never drift. */
export function SidebarNav({ collapsed = false, onNavigate }: SidebarNavProps) {
  return (
    <div className="flex flex-1 flex-col">
      <nav className="flex flex-1 flex-col gap-5 overflow-y-auto px-3 py-4" aria-label="Main">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label}>
            {!collapsed && (
              <p className="mb-1 px-3 font-mono text-[10px] font-medium uppercase tracking-widest text-ink-faint">
                {section.label}
              </p>
            )}
            <div className="flex flex-col gap-0.5">
              {section.items.map((item) => (
                <NavEntry
                  key={item.label}
                  item={item}
                  collapsed={collapsed}
                  onNavigate={onNavigate}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>
      <div className="border-t border-line px-3 py-3">
        <NavEntry item={SETTINGS_ITEM} collapsed={collapsed} onNavigate={onNavigate} />
      </div>
    </div>
  );
}
