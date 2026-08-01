import { cn } from '@/lib/utils';

interface LogoProps {
  className?: string;
  size?: number;
  withWordmark?: boolean;
}

export function Logo({ className, size = 36, withWordmark = false }: LogoProps) {
  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div
        className="relative grid place-items-center rounded-xl bg-gradient-gold shrink-0"
        style={{ width: size, height: size }}
      >
        <svg
          width={size * 0.55}
          height={size * 0.55}
          viewBox="0 0 64 64"
          fill="none"
          aria-hidden="true"
        >
          <path d="M20 44V20h6v18h12v6H20z" fill="#0B0B0B" />
          <circle cx="44" cy="24" r="4" fill="#0B0B0B" />
        </svg>
        <div className="pointer-events-none absolute inset-0 rounded-xl ring-1 ring-white/20" />
      </div>
      {withWordmark && (
        <div className="flex flex-col leading-tight">
          <span className="font-display text-lg font-bold tracking-tight">
            Data<span className="text-gradient-gold">Scribe</span>
          </span>
        </div>
      )}
    </div>
  );
}
