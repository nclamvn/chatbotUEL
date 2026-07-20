import ChatSurface from "@/components/ChatSurface";
import ErrorBoundary from "@/components/ErrorBoundary";

export default function Home() {
  return (
    <ErrorBoundary>
      <ChatSurface />
    </ErrorBoundary>
  );
}
