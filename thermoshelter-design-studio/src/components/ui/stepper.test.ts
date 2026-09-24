import { describe, expect, it } from 'vitest';
import { WORKFLOW_STAGES } from '../../theme/tokens';
import { isStageReachable } from './Stepper';

/**
 * B regression: global stage navigation reachability.
 * - Backward navigation is always free.
 * - Forward clicks are allowed only up to the highest visited stage.
 * - Unavailable stages are never reachable (previously covered by the
 *   expert-mode cases; the rule itself is unchanged).
 */

const idx = (id: string) => WORKFLOW_STAGES.findIndex((s) => s.id === id);
const availableAt = (i: number) => WORKFLOW_STAGES[i].available;

describe('isStageReachable (B: direct stage navigation)', () => {
  it('always allows backward navigation', () => {
    const current = idx('optimization'); // 5
    for (let i = 0; i < current; i++) {
      expect(isStageReachable(i, current, current, availableAt(i))).toBe(true);
    }
  });

  it('blocks strictly-future stages when not yet visited', () => {
    const current = idx('design'); // 2
    const report = idx('report'); // 8
    expect(isStageReachable(report, current, current, availableAt(report))).toBe(false);
  });

  it('allows forward clicks up to the highest visited stage', () => {
    const current = idx('site-climate'); // 0
    const blueprint = idx('blueprint'); // 6
    // Session previously reached Blueprint.
    expect(isStageReachable(blueprint, current, blueprint, availableAt(blueprint))).toBe(true);
    // But not beyond it.
    const report = idx('report');
    expect(isStageReachable(report, current, blueprint, availableAt(report))).toBe(false);
  });

  it('allows an available stage beyond maxVisitedIndex when it has been visited this session', () => {
    const current = idx('site-climate');
    const report = idx('report');
    // Visited this session (maxVisitedIndex >= report): reachable.
    expect(isStageReachable(report, current, report, availableAt(report))).toBe(true);
  });

  it('never allows unavailable stages', () => {
    expect(isStageReachable(3, 0, 8, false)).toBe(false);
  });
});
