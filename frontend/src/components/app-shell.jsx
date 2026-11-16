"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { AppNav } from "@/components/app-nav";

// Wraps every authenticated page: redirects to /login when there's no
// session, otherwise renders the shared nav + page content. Centralizing
// this here means each page doesn't re-implement its own auth check.
export function AppShell({ children }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-blue-50">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          <p className="mt-4 text-sm text-blue-700">Loading&hellip;</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-blue-50">
      <AppNav />
      <main className="flex-1">{children}</main>
    </div>
  );
}
