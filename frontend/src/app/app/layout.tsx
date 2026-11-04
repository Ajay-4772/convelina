import React from "react";
import WorkspaceShell from "../../components/workspace/WorkspaceShell";

export const metadata = {
  title: "Citizen Workspace — CONVELINA",
  description:
    "Indian identity document reconciliation, discrepancy detection, and statutory correction assistance.",
};

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <WorkspaceShell>{children}</WorkspaceShell>;
}

