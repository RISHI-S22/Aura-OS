import React from "react";

export const metadata = {
  title: "AURA - Superintelligence Command Center",
  description: "Autonomous Universal Reasoning Assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0b0f17] text-white min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
