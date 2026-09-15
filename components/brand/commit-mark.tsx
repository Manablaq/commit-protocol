type CommitMarkProps = {
  className?: string;
};

export function CommitMark({
  className = "",
}: CommitMarkProps) {
  return (
    <svg
      className={`commit-mark ${className}`.trim()}
      viewBox="0 0 64 64"
      role="img"
      aria-label="COMMIT"
    >
      <path
        className="commit-mark-primary"
        d="M7 14 30 2v13l-11 6v22l11 6v13L7 50V14Z"
      />
      <path
        className="commit-mark-hot"
        d="M35 17 57 5v16L35 33V17Z"
      />
      <path
        className="commit-mark-cool"
        d="M35 39 57 27v16L35 55V39Z"
      />
      <path
        className="commit-mark-seam"
        d="m25 27 8-4 7 4-8 5 8 5-7 4-8-5 7-4-7-5Z"
      />
    </svg>
  );
}
