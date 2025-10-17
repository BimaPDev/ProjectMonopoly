export default function LandingPage() {
  return (
    <div
      className="flex items-center justify-center min-h-screen text-white bg-black"

    >
      <div className="container flex flex-col items-center px-4 py-12 mx-auto">
        <div className="w-full max-w-md mb-12">
          <img
            src="https://dogwoodgaming.com/wp-content/uploads/2021/12/dogwood-gaming-logo.png"
            alt="Dogwood Gaming Logo"
            className="object-contain w-full"
          />
        </div>

        <div className="mb-16 text-center">
          <h1 className="mb-6 text-5xl font-extrabold tracking-wide text-transparent text-white bg-clip-text">
            Marketing Tool
          </h1>
          <p className="max-w-2xl mx-auto text-xl text-gray-300">
            Elevate your brand with Dogwood Gaming's professional marketing suite.
          </p>
        </div>

        {/* Card with buttons */}
        <div className="w-full max-w-md p-8">
          <h2 className="mb-6 text-2xl font-bold text-center">Ready to Level Up?</h2>

          <div className="space-y-4">
            <a
              href="/login"
              className="block w-full px-6 py-3 font-semibold text-center text-white border border-white hover:border-purple-500 "
            >
              Sign In
            </a>

            <a
              href="/register"
              className="block w-full px-6 py-3 font-semibold text-center text-white border border-white hover:border-purple-500"
            >
              Create Account
            </a>
          </div>
        </div>


        <div className="mt-16 text-sm text-center text-gray-500">
          <p>© 2025 Dogwood Gaming. All rights reserved.</p>
          <span>
            <a
              href="https://dogwoodgaming.com/"
              className="transition-all duration-200 hover:text-purple-400 hover:underline"
            >
              Home page
            </a> | <a
              href="https://dogwoodgaming.com/contact-us/"
              className="transition-all duration-200 hover:text-purple-400 hover:underline"
            >
              Contact us
            </a>
          </span>
        </div>
      </div>
    </div>
  );
}