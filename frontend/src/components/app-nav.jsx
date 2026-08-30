"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { FileText, LayoutDashboard, LogOut, Menu, Upload as UploadIcon, X } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const NAV_LINKS = [
  { href: "/dashboard", label: "Companies", icon: LayoutDashboard },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/upload", label: "Upload Report", icon: UploadIcon },
];

function initialsFor(name) {
  if (!name) return "?";
  return name
    .trim()
    .split(/\s+/)
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function AppNav() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    router.replace("/login");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-blue-100 bg-blue-100/95 backdrop-blur">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/dashboard" className="flex items-center gap-2 text-xl font-bold">
          <Image
            src="/favicon.ico"
            alt="FinAI Analyzer"
            width={32}
            height={32}
            className="h-8 w-8 rounded-md"
            priority
          />
          <span className="text-blue-600">FinAI</span>
          <span className="text-blue-900">Analyzer</span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`text-sm font-medium uppercase tracking-wide transition-colors ${
                pathname?.startsWith(href) ? "text-blue-600" : "text-blue-800 hover:text-blue-600"
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>

        <div className="relative hidden md:block" ref={menuRef}>
          <button
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Open account menu"
            aria-expanded={menuOpen}
            className="flex items-center gap-2 rounded-full border border-blue-200 bg-white px-2 py-1 text-sm font-medium text-blue-900 hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-600 text-xs font-semibold text-white">
              {initialsFor(user?.name)}
            </span>
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-12 w-56 rounded-md border border-blue-100 bg-white py-1 shadow-lg">
              <div className="border-b border-blue-50 px-3 py-2">
                <p className="truncate text-sm font-medium text-blue-900">{user?.name}</p>
                <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <Link
                href="/reports"
                className="block px-3 py-2 text-sm text-blue-900 hover:bg-blue-50"
                onClick={() => setMenuOpen(false)}
              >
                Profile
              </Link>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50"
              >
                <LogOut className="h-4 w-4" /> Sign out
              </button>
            </div>
          )}
        </div>

        <button
          className="md:hidden"
          onClick={() => setMobileOpen((v) => !v)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
        >
          {mobileOpen ? <X className="h-5 w-5 text-blue-900" /> : <Menu className="h-5 w-5 text-blue-900" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="space-y-1 border-t border-blue-100 bg-blue-50 px-4 py-3 md:hidden">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setMobileOpen(false)}
              className="block rounded-md px-3 py-2 text-sm font-medium uppercase tracking-wide text-blue-900 hover:bg-blue-100"
            >
              {label}
            </Link>
          ))}
          <div className="mt-2 border-t border-blue-100 pt-2">
            <p className="truncate px-3 text-xs text-muted-foreground">{user?.email}</p>
            <button
              onClick={handleLogout}
              className="mt-1 flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-red-600 hover:bg-red-100"
            >
              <LogOut className="h-4 w-4" /> Sign out
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
