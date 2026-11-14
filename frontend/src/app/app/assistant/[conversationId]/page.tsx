"use client";

import React from "react";
import { useParams } from "next/navigation";
import AssistantWorkspace from "../../../../components/assistant/AssistantWorkspace";

export default function ConversationPage() {
  const params = useParams();
  const rawId = params?.conversationId;
  const conversationId = Array.isArray(rawId) ? rawId[0] : (rawId as string | undefined);

  return <AssistantWorkspace initialConversationId={conversationId} />;
}
