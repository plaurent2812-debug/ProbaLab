import { Sparkles } from 'lucide-react';
import type { UserRole } from '../../../types/v2/common';
import type { AnalysisPayload } from '../../../types/v2/match-detail';
import { LockOverlay } from '../system/LockOverlay';

export interface AIAnalysisProps {
  analysis: AnalysisPayload;
  userRole: UserRole;
  'data-testid'?: string;
}

const UPGRADE_MESSAGE = "Débloque l'analyse complète avec Premium";
const SIGNUP_MESSAGE = 'Crée un compte pour accéder à l’analyse IA';

function Paragraphs({ paragraphs }: { paragraphs: string[] }) {
  return (
    <>
      {paragraphs.map((p, i) => (
        <p
          key={i}
          className="mb-2 text-sm leading-relaxed last:mb-0"
          style={{ color: 'var(--text-muted)' }}
        >
          {p}
        </p>
      ))}
    </>
  );
}

export function AIAnalysis({
  analysis,
  userRole,
  'data-testid': dataTestId = 'ai-analysis',
}: AIAnalysisProps) {
  const { paragraphs } = analysis;
  const isVisitor = userRole === 'visitor';
  const isFree = userRole === 'free';

  if (isVisitor) {
    return (
      <section
        data-testid={dataTestId}
        className="rounded-[22px] p-4"
        style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}
      >
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold" style={{ color: 'var(--text)' }}>
          <Sparkles className="h-4 w-4" style={{ color: 'var(--primary)' }} aria-hidden="true" />
          Analyse IA
        </h3>
        <LockOverlay message={SIGNUP_MESSAGE}>
          <Paragraphs paragraphs={paragraphs} />
        </LockOverlay>
      </section>
    );
  }

  const [first, ...rest] = paragraphs;
  const gated = isFree && rest.length > 0;

  return (
    <section
      data-testid={dataTestId}
      className="rounded-[22px] p-4"
      style={{ border: '1px solid var(--border)', background: 'var(--surface)' }}
    >
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold" style={{ color: 'var(--text)' }}>
        <Sparkles className="h-4 w-4" style={{ color: 'var(--primary)' }} aria-hidden="true" />
        Analyse IA
      </h3>
      {first && (
        <p className="mb-2 text-sm leading-relaxed" style={{ color: 'var(--text)' }}>
          {first}
        </p>
      )}
      {rest.length > 0 &&
        (gated ? (
          <div className="relative mt-2">
            <LockOverlay message={UPGRADE_MESSAGE}>
              <Paragraphs paragraphs={rest} />
            </LockOverlay>
          </div>
        ) : (
          <Paragraphs paragraphs={rest} />
        ))}
    </section>
  );
}

export default AIAnalysis;
