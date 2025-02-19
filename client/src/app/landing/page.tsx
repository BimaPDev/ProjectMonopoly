export default function LandingPage() {
  return (
    <div
      className="flex flex-col items-center justify-center min-h-screen text-white px-6"
      style={{
        background: "linear-gradient(-60deg, rgb(189, 189, 189),rgb(175, 148, 237), rgb(79, 79, 79))",
      }}
    >
      <div>
              <img 
                src="https://dogwoodgaming.com/wp-content/uploads/2021/12/dogwood-gaming-logo.png" 
                alt="Login Visual"
                className="w-full h-full object-cover"
              />
      </div>
      <h1 className="text-4xl font-extrabold tracking-wide">Welcome to Dogwood Gaming's marketing tool.</h1>
      
      <a
        href="/login"
        className="mt-6 px-6 py-3 bg-white text-black font-semibold rounded-md shadow-md transition hover:bg-gray-300 hover:shadow-lg"
      >
        Get Started
      </a>
    </div>
  );
}
