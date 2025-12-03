 "use client";

import dynamic from "next/dynamic";

const Text = dynamic(() => import("./components/text"), { ssr: false });

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-4xl px-4">
        <Text />
      </div>
    </main>
  );
}
