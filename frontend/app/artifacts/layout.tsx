import type { ReactNode } from "react";
import { AppShell } from "@/components/layout/app-shell";

export default function ArtifactsLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
