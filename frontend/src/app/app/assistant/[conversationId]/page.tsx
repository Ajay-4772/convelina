"use client";

import React from "react";
import { useParams } from "next/navigation";
import AssistantWorkspace from "../../../../components/assistant/AssistantWorkspace";

export default function IndividualConversationPage() {
  const params = useParams();
  const conversationId = params?.conversationId as string;

  return <AssistantWorkspace initialConversationId={conversationId} />;
}

