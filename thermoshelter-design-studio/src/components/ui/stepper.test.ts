import { describe, expect, it } from 'vitest';
import { WORKFLOW_STAGES } from '../../theme/tokens';
import { isStageReachable } from './Stepper';

/**
 * B regression: global stage navigation reachability.
 * - Backward navigation is always free.
 * - Guided mode: forward clicks allowed only up to the highest visited stage.
 * - Expert mode: every available stage is directly clickable.
 */

const idx = (id: string) => WORKFLOW_STAGES.findIndex((s) => s.id === id);
const availableAt = (i: number) => WORKFLOW_STAGES[i].available;

describe('isStageReachable (B: direct stage navigation)', () => {
  it('always allows backward navigation in guided mode', () => {
    const current = idx('optimization'); // 5
    for (let i = 0; i < current; i++) {
      expect(isStageReachable(i, current, current, availableAt(i), false)).toBe(true);
    }
  });

  it('blocks strictly-future stages in guided mode when not yet visited', () => {
    const current = idx('design'); // 2
    const report = idx('report'); // 8
    expect(isStageReachable(report, current, current, availableAt(report), false)).toBe(false);
  });

  it('allows forward clicks up to the highest visited stage in guided mode', () => {
    const current = idx('site-climate'); // 0
    const blueprint = idx('blueprint'); // 6
    // Session previously reached Blueprint.
    expect(isStageReachable(blueprint, current, blueprint, availableAt(blueprint), false)).toBe(true);
    // But not beyond it.
    const report = idx('report');
    expect(isStageReachable(report, current, blueprint, availableAt(report), false)).toBe(false);
  });

  it('allows every available stage in expert mode', () => {
    const current = idx('site-climate');
    const report = idx('report');
    expect(isStageReachable(report, current, current, availableAt(report), true)).toBe(true);
  });

  it('never allows unavailable stages in any mode', () => {
    expect(isStageReachable(3, 0, 8, false, true)).toBe(false);
    expect(isStageReachable(3, 0, 8, false, false)).toBe(false);
  });
});
