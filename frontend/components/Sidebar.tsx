"use client";

import { useState } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  ChartNoAxesCombined,
  LayoutDashboard,
  List,
  Upload,
  Wallet,
  LogOut,
  Menu,
  X,
} from "lucide-react";

type SidebarProps = {
  userEmail: string | null;
  onLogout: () => void;
};

export default function Sidebar({ userEmail, onLogout }: SidebarProps) {
  const pathname = usePathname();

  const [isOpen, setIsOpen] = useState(false);

  function linkClass(href: string) {
    const isActive =
      href === "/" ? pathname === "/" : pathname.startsWith(href);

    return [
      "flex items-center gap-3 rounded-xl px-4 py-3 font-medium transition",
      isActive
        ? "bg-blue-50 text-blue-600"
        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
    ].join(" ");
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        aria-label="Open navigation"
        className="absolute left-4 top-4 z-40 flex h-11 w-11 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm md:hidden"
      >
        <Menu size={22} />
      </button>

      {isOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
        />
      )}

      <aside
        className={`
                    fixed inset-y-0 left-0 z-50 w-64 border-r border-slate-200 bg-white px-5 py-7
                    transition-transform duration-200
                    md:sticky md:top-0 md:h-screen md:self-start md:z-auto md:shrink-0 md:translate-x-0
                    ${isOpen ? "translate-x-0" : "-translate-x-full"}
                `}
      >
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          aria-label="Close navigation"
          className="absolute right-4 top-4 flex h-9 w-9 items-center justify-center text-slate-500 md:hidden"
        >
          <X size={22} />
        </button>

        <div className="mb-8 flex items-center gap-3 px-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
            <ChartNoAxesCombined size={22} />
          </div>

          <div>
            <h1 className="text-lg font-bold text-slate-900">
              Trading Journal
            </h1>

            <p className="text-xs text-slate-500">Performance tracker</p>
          </div>
        </div>

        <nav className="flex flex-col gap-2">
          <Link
            href="/"
            className={linkClass("/")}
            onClick={() => setIsOpen(false)}
          >
            <LayoutDashboard size={20} />
            Dashboard
          </Link>

          <Link
            href="/trades"
            className={linkClass("/trades")}
            onClick={() => setIsOpen(false)}
          >
            <List size={20} />
            Trades
          </Link>

          <Link
            href="/import"
            className={linkClass("/import")}
            onClick={() => setIsOpen(false)}
          >
            <Upload size={20} />
            Import CSV
          </Link>

          <Link
            href="/accounts"
            className={linkClass("/accounts")}
            onClick={() => setIsOpen(false)}
          >
            <Wallet size={20} />
            Accounts
          </Link>
        </nav>

        <div className="mt-8 border-t border-slate-200 px-2 pt-5">
          <p className="truncate text-xs text-slate-500">{userEmail}</p>

          <button
            type="button"
            onClick={onLogout}
            className="mt-3 flex cursor-pointer items-center gap-2 text-sm text-slate-500 transition hover:text-slate-900"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>
    </>
  );
}
