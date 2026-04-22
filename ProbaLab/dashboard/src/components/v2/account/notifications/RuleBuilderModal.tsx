import { useEffect, useMemo, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { X } from 'lucide-react';
import { Modal } from '@/components/v2/system/Modal';
import {
  notificationRuleSchema,
  type ConditionType,
  type NotificationRule,
  type RuleChannel,
  type RuleCondition,
} from '@/lib/v2/schemas/rules';
import {
  useCreateRule,
  useUpdateRule,
  type CreateRuleInput,
} from '@/hooks/v2/useNotificationRules';
import { ConditionValueField, LEAGUE_OPTIONS } from './conditionFields';

export interface RuleBuilderModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialRule?: NotificationRule;
  onSaved?: (rule: NotificationRule) => void;
  'data-testid'?: string;
}

const CONDITION_TYPE_OPTIONS: readonly {
  value: ConditionType;
  label: string;
}[] = [
  { value: 'edge_min', label: 'Edge minimum' },
  { value: 'league_in', label: 'Ligues' },
  { value: 'sport', label: 'Sport' },
  { value: 'confidence', label: 'Confiance' },
  { value: 'kickoff_within', label: "Coup d'envoi dans (heures)" },
  { value: 'bankroll_drawdown', label: 'Drawdown bankroll' },
];

/** Build a fresh condition with a sensible default value for a given type. */
function blankCondition(type: ConditionType): RuleCondition {
  if (type === 'edge_min') return { type, value: 5 };
  if (type === 'league_in') return { type, value: [LEAGUE_OPTIONS[0].value] };
  if (type === 'sport') return { type, value: 'football' };
  if (type === 'confidence') return { type, value: 'HIGH' };
  if (type === 'kickoff_within') return { type, value: 2 };
  return { type, value: 10 };
}

function emptyRule(): CreateRuleInput {
  return {
    name: '',
    conditions: [blankCondition('edge_min')],
    logic: 'AND',
    channels: [],
    action: { notify: true, pauseSuggestion: false },
    enabled: true,
  };
}

/**
 * Composable rule builder. Lets the user define up to three conditions
 * combined via AND/OR and choose the notification channels. Uses
 * react-hook-form with a zod resolver so the validation errors come
 * straight from `notificationRuleSchema` and stay in sync with the API
 * contract.
 *
 * The modal is created (no `initialRule`) or edited (with `initialRule`).
 * On success, the parent receives `onOpenChange(false)` and the rules
 * query cache is invalidated by the underlying mutation hook.
 */
export function RuleBuilderModal({
  open,
  onOpenChange,
  initialRule,
  onSaved,
  'data-testid': dataTestId = 'rule-builder-modal',
}: RuleBuilderModalProps) {
  const createMut = useCreateRule();
  const updateMut = useUpdateRule(initialRule?.id ?? '');
  const isEdit = Boolean(initialRule?.id);
  const [apiError, setApiError] = useState<string | null>(null);

  const defaultValues = useMemo<CreateRuleInput>(
    () => (initialRule ? { ...initialRule } : emptyRule()),
    [initialRule],
  );

  const form = useForm<CreateRuleInput>({
    resolver: zodResolver(notificationRuleSchema),
    defaultValues,
    mode: 'onSubmit',
  });

  // Reset when the modal is (re)opened with a different initial rule.
  useEffect(() => {
    if (!open) return;
    form.reset(defaultValues);
    setApiError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, initialRule?.id]);

  const conditions = form.watch('conditions');
  const channels = form.watch('channels');
  const logic = form.watch('logic');
  const pauseSuggestion = form.watch('action.pauseSuggestion');
  const enabled = form.watch('enabled');

  const addCondition = () => {
    if (conditions.length >= 3) return;
    form.setValue(
      'conditions',
      [...conditions, blankCondition('edge_min')],
      { shouldValidate: false },
    );
  };

  const removeCondition = (index: number) => {
    if (conditions.length <= 1) return;
    form.setValue(
      'conditions',
      conditions.filter((_, i) => i !== index),
      { shouldValidate: false },
    );
  };

  const updateConditionType = (index: number, type: ConditionType) => {
    form.setValue(`conditions.${index}`, blankCondition(type), {
      shouldValidate: false,
    });
  };

  const toggleChannel = (c: RuleChannel) => {
    const current = channels ?? [];
    const next = current.includes(c)
      ? current.filter((x) => x !== c)
      : [...current, c];
    form.setValue('channels', next, { shouldValidate: false });
  };

  const onSubmit = form.handleSubmit(async (values) => {
    setApiError(null);
    try {
      if (isEdit && initialRule?.id) {
        const saved = await updateMut.mutateAsync({
          ...values,
          id: initialRule.id,
        });
        onSaved?.(saved);
      } else {
        const saved = await createMut.mutateAsync(values);
        onSaved?.(saved);
      }
      onOpenChange(false);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Erreur lors de l'enregistrement";
      setApiError(message);
    }
  });

  const title = isEdit ? 'Modifier la règle' : 'Nouvelle règle';
  const description = isEdit
    ? "Ajuste quand et comment ProbaLab t'envoie cette alerte."
    : "Définis quand et comment ProbaLab t'envoie une alerte.";
  const nameError = form.formState.errors.name?.message;
  const channelsError = form.formState.errors.channels?.message as
    | string
    | undefined;
  const isPending = createMut.isPending || updateMut.isPending;

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      description={description}
      data-testid={dataTestId}
      footer={
        <>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Annuler
          </button>
          <button
            type="submit"
            form="rule-builder-form"
            disabled={isPending}
            className="inline-flex items-center rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isPending ? 'Enregistrement…' : 'Enregistrer la règle'}
          </button>
        </>
      }
    >
      <form
        id="rule-builder-form"
        onSubmit={onSubmit}
        className="space-y-5"
        noValidate
      >
        <div>
          <label
            htmlFor="rule-name"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Nom de la règle
          </label>
          <input
            id="rule-name"
            type="text"
            {...form.register('name')}
            aria-invalid={nameError ? 'true' : 'false'}
            className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          />
          {nameError && (
            <p className="mt-1 text-xs text-rose-600" role="alert">
              {nameError}
            </p>
          )}
        </div>

        <fieldset className="border-none p-0">
          <legend className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            Quand…
          </legend>
          <div className="mt-2 space-y-3">
            {conditions.map((c, i) => (
              <div
                key={i}
                data-testid="rule-condition-row"
                className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3 sm:flex-row sm:items-start dark:border-slate-800 dark:bg-slate-900/40"
              >
                <div className="flex-1 space-y-2">
                  <label
                    htmlFor={`rule-cond-type-${i}`}
                    className="block text-xs font-medium text-slate-500 dark:text-slate-400"
                  >
                    {`Type condition ${i + 1}`}
                  </label>
                  <select
                    id={`rule-cond-type-${i}`}
                    value={c.type}
                    onChange={(e) =>
                      updateConditionType(i, e.target.value as ConditionType)
                    }
                    className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                  >
                    {CONDITION_TYPE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>

                  <Controller
                    control={form.control}
                    name={`conditions.${i}`}
                    render={({ field }) => (
                      <ConditionValueField
                        index={i}
                        condition={field.value}
                        onChange={field.onChange}
                      />
                    )}
                  />
                </div>
                {conditions.length > 1 && (
                  <button
                    type="button"
                    aria-label={`Supprimer condition ${i + 1}`}
                    onClick={() => removeCondition(i)}
                    className="mt-6 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-slate-400 hover:bg-rose-50 hover:text-rose-600 focus-visible:outline focus-visible:outline-2 dark:hover:bg-rose-950"
                  >
                    <X className="h-4 w-4" aria-hidden="true" />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={addCondition}
            disabled={conditions.length >= 3}
            className="mt-3 inline-flex items-center gap-1 rounded-lg border border-dashed border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:border-emerald-500 hover:text-emerald-600 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:text-slate-400"
          >
            + Ajouter une condition
          </button>
        </fieldset>

        {conditions.length > 1 && (
          <fieldset className="border-none p-0">
            <legend className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              Relier avec…
            </legend>
            <div
              className="mt-2 inline-flex overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700"
              role="group"
              aria-label="Relier les conditions"
            >
              {(['AND', 'OR'] as const).map((l) => {
                const isActive = logic === l;
                return (
                  <button
                    key={l}
                    type="button"
                    aria-pressed={isActive}
                    onClick={() =>
                      form.setValue('logic', l, { shouldValidate: false })
                    }
                    className={
                      isActive
                        ? 'bg-emerald-500 px-4 py-1.5 text-xs font-medium text-white'
                        : 'bg-white px-4 py-1.5 text-xs font-medium text-slate-600 dark:bg-slate-900 dark:text-slate-300'
                    }
                  >
                    {l}
                  </button>
                );
              })}
            </div>
          </fieldset>
        )}

        <fieldset className="border-none p-0">
          <legend className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            Notifier sur…
          </legend>
          <div className="mt-2 flex flex-wrap gap-3">
            {(
              [
                { value: 'telegram' as const, label: 'Telegram' },
                { value: 'email' as const, label: 'Email' },
                { value: 'push' as const, label: 'Push' },
              ]
            ).map((opt) => {
              const id = `rule-channel-${opt.value}`;
              const isChecked = (channels ?? []).includes(opt.value);
              return (
                <label
                  key={opt.value}
                  htmlFor={id}
                  className="inline-flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200"
                >
                  <input
                    id={id}
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleChannel(opt.value)}
                    className="h-4 w-4 rounded border-slate-300 text-emerald-500 focus:ring-emerald-500"
                  />
                  {opt.label}
                </label>
              );
            })}
          </div>
          {channelsError && (
            <p className="mt-1 text-xs text-rose-600" role="alert">
              {channelsError}
            </p>
          )}
        </fieldset>

        <label
          htmlFor="rule-pause-suggestion"
          className="inline-flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200"
        >
          <input
            id="rule-pause-suggestion"
            type="checkbox"
            checked={pauseSuggestion}
            onChange={(e) =>
              form.setValue('action.pauseSuggestion', e.target.checked, {
                shouldValidate: false,
              })
            }
            className="h-4 w-4 rounded border-slate-300 text-emerald-500 focus:ring-emerald-500"
          />
          Suggérer pause paris à l&apos;utilisateur
        </label>

        <div className="flex items-center justify-between gap-3">
          <label
            htmlFor="rule-enabled"
            className="text-sm text-slate-700 dark:text-slate-200"
          >
            Activer la règle
          </label>
          <button
            id="rule-enabled"
            type="button"
            role="switch"
            aria-checked={enabled}
            aria-label="Activer la règle"
            onClick={() =>
              form.setValue('enabled', !enabled, { shouldValidate: false })
            }
            className={
              enabled
                ? 'relative inline-flex h-5 w-9 items-center rounded-full bg-emerald-500 transition'
                : 'relative inline-flex h-5 w-9 items-center rounded-full bg-slate-300 transition dark:bg-slate-700'
            }
          >
            <span
              className={
                enabled
                  ? 'block h-4 w-4 translate-x-4 rounded-full bg-white transition-transform'
                  : 'block h-4 w-4 translate-x-0.5 rounded-full bg-white transition-transform'
              }
            />
          </button>
        </div>

        {apiError && (
          <div
            role="alert"
            className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-300"
          >
            {apiError}
          </div>
        )}
      </form>
    </Modal>
  );
}

export default RuleBuilderModal;
