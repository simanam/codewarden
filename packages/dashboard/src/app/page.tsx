export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-5xl font-bold mb-4">
          <span className="text-primary-500">Code</span>Warden
        </h1>
        <p className="text-xl text-secondary-400 mb-8">
          You ship the code. We stand guard.
        </p>
        <div className="flex gap-4 justify-center">
          <a
            href="/login"
            className="px-6 py-3 bg-primary-600 hover:bg-primary-700 rounded-lg font-medium transition-colors"
          >
            Get Started
          </a>
          <a
            href="/docs"
            className="px-6 py-3 bg-secondary-800 hover:bg-secondary-700 rounded-lg font-medium transition-colors"
          >
            Documentation
          </a>
        </div>
      </div>
    </main>
  );
}
