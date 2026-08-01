import { motion } from 'framer-motion';

export function AnimatedBackground() {
  return (
    // 🛠️ Removed -z-10 and bg-background so it no longer hides behind your main layout
    <div className="pointer-events-none fixed inset-0 overflow-hidden">
      
      {/* Subtle Data Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px] dark:bg-[linear-gradient(to_right,#ffffff0a_1px,transparent_1px),linear-gradient(to_bottom,#ffffff0a_1px,transparent_1px)]"></div>

      {/* Floating Agent / Data Nodes */}
      <motion.div
        animate={{
          x: [0, 100, -50, 0],
          y: [0, 50, 100, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear"
        }}
        className="absolute -top-[10%] -left-[10%] h-[40rem] w-[40rem] rounded-full bg-gold-500/10 blur-[100px] dark:bg-gold-500/5"
      />
      
      <motion.div
        animate={{
          x: [0, -100, 50, 0],
          y: [0, -50, -100, 0],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "linear"
        }}
        className="absolute top-[20%] -right-[10%] h-[35rem] w-[35rem] rounded-full bg-zinc-400/20 blur-[100px] dark:bg-zinc-600/10"
      />
    </div>
  );
}