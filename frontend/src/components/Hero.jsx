const Hero = () => {
  return (
    <div className="bg-gradient-to-r from-purple-50 to-white p-10 rounded-2xl mt-6">
      <div className="flex justify-between items-center">
        
        <div>
          <h1 className="text-5xl font-bold text-gray-800">
            Discover Products <br />
            <span className="text-purple-600">Tailored for You</span>
          </h1>

          <p className="mt-4 text-gray-500">
            Discover the best products tailored just for you.
          </p>

          <button className="mt-6 bg-purple-600 text-white px-6 py-3 rounded-xl">
            Browse Categories
          </button>
        </div>

        <img
          src="https://via.placeholder.com/400"
          className="w-[350px]"
        />
      </div>
    </div>
  );
};

export default Hero;