export default function LandingPage() {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <h1 className="text-4xl font-bold">Welcome to My Website</h1>
        <p className="text-lg text-gray-600">The best marketing tool for your needs</p>
        <a href="/login" className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-md">
          Get Started
        </a>
      </div>
    );
  }
  