export interface TrialBannerProps {
  daysLeft: number;
  endDate?: string;
}

export function TrialBanner({ daysLeft, endDate }: TrialBannerProps) {
  return (
    <div role="region" aria-label="Trial banner">
      <span>Trial premium · J-{daysLeft}</span>
      {endDate && <span> · jusqu'au {endDate}</span>}
    </div>
  );
}

export default TrialBanner;
