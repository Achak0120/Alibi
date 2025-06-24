import React from 'react';
import { motion } from 'framer-motion';
import { Languages, CheckCircle, ShieldCheck } from 'lucide-react';

const featureList = [
  {
    icon: Languages,
    title: "Multi-Language Support",
    description: "Translate to 10+ languages including Spanish, Hindi, Chinese, and more.",
    color: "blue"
  },
  {
    icon: CheckCircle,
    title: "Accurate Translation",
    description: "AI-powered translation specifically trained for legal and medical documents.",
    color: "green"
  },
  {
    icon: ShieldCheck,
    title: "Secure & Private",
    description: "Your documents are processed securely and never stored on our servers.",
    color: "purple"
  }
];

const FeatureCard = ({ icon: Icon, title, description, color, index }) => {
  const colors = {
    blue: "text-blue-400",
    green: "text-green-400",
    purple: "text-purple-400",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 + index * 0.1 }}
      className="text-center p-6 glass-card rounded-lg"
    >
      <div className="w-12 h-12 bg-background rounded-lg flex items-center justify-center mx-auto mb-4 border border-white/10">
        <Icon className={`w-6 h-6 ${colors[color]}`} />
      </div>
      <h3 className="font-semibold text-gray-100 mb-2">{title}</h3>
      <p className="text-sm text-gray-400">{description}</p>
    </motion.div>
  );
};

const Features = () => {
  return (
    <div className="my-16 grid grid-cols-1 md:grid-cols-3 gap-8">
      {featureList.map((feature, index) => (
        <FeatureCard key={index} {...feature} index={index} />
      ))}
    </div>
  );
};

export default Features;