const sizes = {
  sm: 'h-5 w-5',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

const colors = {
  amber: 'border-amber-500',
  blue: 'border-blue-400',
  dark: 'border-zinc-950',
};

const LoadingSpinner = ({ size = 'lg', color = 'amber', fullPage = false, message = null }) => {
  const spinner = (
    <div className={`animate-spin rounded-full border-b-2 ${sizes[size]} ${colors[color]}`} />
  );

  if (!fullPage) return spinner;

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
      {message ? (
        <div className="text-center">
          <div className="mx-auto mb-4 flex justify-center">{spinner}</div>
          <p className="text-zinc-400">{message}</p>
        </div>
      ) : spinner}
    </div>
  );
};

export default LoadingSpinner;
