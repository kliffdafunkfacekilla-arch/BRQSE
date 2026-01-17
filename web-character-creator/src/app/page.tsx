
import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'radial-gradient(circle at 50% 50%, rgba(0, 242, 255, 0.1) 0%, transparent 70%)'
      }}></div>

      <div className="glass-panel p-8 md:p-12 text-center max-w-lg w-[90%] z-10 animate-[fadeIn_1s_ease-out]">
        <h1 className="text-4xl md:text-6xl mb-4 title-gradient uppercase tracking-widest">
          Project B.R.Q.S.E.
        </h1>
        <p className="text-gray-400 mb-8 text-lg font-light">
          Biological Reconnaissance & Quantum Simulation Engine
        </p>

        <div className="space-y-4">
          <Link href="/create">
            <button className="btn-primary w-full text-xl py-4">
              Initialize New Host
            </button>
          </Link>

          <div className="flex gap-4 justify-center mt-6">
            <button className="text-sm text-gray-500 hover:text-white transition">Load Profile</button>
            <button className="text-sm text-gray-500 hover:text-white transition">Settings</button>
          </div>
        </div>
      </div>

      <div className="absolute bottom-4 text-xs text-gray-700">
        v2.0.0 // Web Client // Mobile Optimized
      </div>
    </main>
  );
}
