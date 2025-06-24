import React from 'react';
import { motion } from 'framer-motion';

const Hero = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="text-center my-12 sm:my-16"
    >
      <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 mb-4">
        Clarity in Every Word
      </h2>
      <p className="text-lg text-gray-300 max-w-3xl mx-auto">
        Instantly translate legal, medical, and financial documents. Then, ask questions and get easy-to-understand answers from our AI.
      </p>
    </motion.div>
  );
};

export default Hero;