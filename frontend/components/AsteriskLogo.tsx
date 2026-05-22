export function AsteriskLogo({ size = 32 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Eight-pointed asterisk / snowflake */}
      {[0, 45, 90, 135, 180, 225, 270, 315].map((angle) => (
        <rect
          key={angle}
          x="15"
          y="4"
          width="2"
          height="24"
          rx="1"
          fill="#CC6B3F"
          transform={`rotate(${angle} 16 16)`}
        />
      ))}
    </svg>
  );
}
