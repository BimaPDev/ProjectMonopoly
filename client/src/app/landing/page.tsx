export default function LandingPage() {
  return (
    <div
      className="flex flex-col items-center justify-center min-h-screen text-white px-6"
      style={{
        background: "linear-gradient(-60deg, rgb(36, 36, 36), rgb(0, 0, 0))",
      }}
    >
      <h1 className="text-4xl font-extrabold tracking-wide">Welcome to Dogwood Gaming's marketing tool.</h1>
      <p className="text-lg text-gray-400 mt-3">Log in below</p>
      <a
        href="/login"
        className="mt-6 px-6 py-3 bg-white text-black font-semibold rounded-md shadow-md transition hover:bg-gray-300 hover:shadow-lg"
      >
        Get Started
      </a>
    </div>
  );
}
