import type { ReactNode } from "react";
import { AppShell } from "@/components/layout/app-shell";

export default function ImportLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
